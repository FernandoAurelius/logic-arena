from ninja import Header, Router

from apps.accounts.application.services import require_session
from apps.accounts.schemas import ErrorSchema
from apps.arena.models import Exercise
from apps.arena.schemas import ExerciseExplanationSchema, TrackDetailSchema
from apps.arena.services import build_exercise_catalog_meta
from apps.learning.application.services import build_explanation_blueprint_for_exercise, ensure_exercise_explanation
from apps.learning.selectors import get_track_by_slug
from apps.progress.application.services import build_track_progress_summary


router = Router(tags=['learning'])


def _collapse_inline(value: str) -> str:
    return ' '.join(part.strip() for part in str(value).splitlines() if part.strip())


def _format_objective_marker(raw: str, index: int) -> str:
    cleaned = raw.strip()
    if len(cleaned) == 1 and cleaned.isalpha():
        return cleaned.upper()
    return chr(65 + (index % 26))


def _build_objective_explanation_payload(exercise: Exercise) -> dict:
    workspace_spec = exercise.workspace_spec or {}
    evaluation_plan = exercise.evaluation_plan or {}
    raw_options = workspace_spec.get('options', [])
    correct_options = {
        str(option).strip().lower()
        for option in evaluation_plan.get('correct_options', [])
        if str(option).strip()
    }

    distractor_rationales = []
    answer_rationale = ''
    question_focus = _collapse_inline(
        exercise.pedagogical_brief
        or exercise.concept_summary
        or exercise.statement
    )

    if isinstance(raw_options, list):
        for index, raw_option in enumerate(raw_options):
            if not isinstance(raw_option, dict):
                continue
            key = str(raw_option.get('canonical_key') or raw_option.get('key') or '').strip()
            label = str(raw_option.get('label') or key or '').strip()
            marker = _format_objective_marker(label or key, index)
            text = _collapse_inline(
                raw_option.get('text')
                or raw_option.get('content')
                or raw_option.get('value')
                or raw_option.get('title')
                or label
                or key
                or 'Alternativa'
            )
            explanation = _collapse_inline(raw_option.get('explanation') or '')
            is_correct = (
                bool(raw_option.get('is_correct'))
                or bool(raw_option.get('correct'))
                or key.lower() in correct_options
                or label.lower() in correct_options
            )
            payload = {
                'key': key or label or marker.lower(),
                'marker': marker,
                'text': text,
                'explanation': explanation,
                'is_correct': is_correct,
            }
            if is_correct and not answer_rationale:
                answer_rationale = (
                    f'**{marker}. {text}** é a correta.'
                    + (f' {explanation}' if explanation else '')
                )
            elif not is_correct:
                distractor_rationales.append(payload)

    return {
        'presentation_mode': 'objective_review',
        'question_focus': question_focus,
        'answer_rationale': answer_rationale,
        'distractor_rationales': distractor_rationales,
    }


@router.get('/tracks/{track_slug}', response={200: TrackDetailSchema, 401: ErrorSchema, 404: ErrorSchema}, summary='Retorna a página de trilha com progresso, conceitos e exercícios.')
def get_track_detail(request, track_slug: str, authorization: str | None = Header(default=None)):
    try:
        session = require_session(authorization)
    except PermissionError as error:
        return 401, {'message': str(error)}

    track = get_track_by_slug(track_slug)
    if track is None:
        return 404, {'message': 'Trilha não encontrada.'}

    summary = build_track_progress_summary(track, session.user)
    current_target = summary['current_target']
    exercises = []
    first_unfinished_seen = False

    for index, exercise in enumerate(summary['exercises'], start=1):
        progress = summary['progress_index'].get(exercise.id)
        meta = build_exercise_catalog_meta(exercise)
        passed_once = bool(progress and 'passed_once' in (progress.awarded_progress_markers or []))
        attempts_count = progress.attempts_count if progress else 0

        if passed_once:
            status = 'passed'
        elif not first_unfinished_seen:
            status = 'in_progress' if attempts_count > 0 else 'available'
            first_unfinished_seen = True
        else:
            status = 'locked'

        exercises.append(
            {
                **serialize_exercise_summary(exercise),
                'position': index,
                'pedagogical_brief': meta['pedagogical_brief'],
                'is_current_target': current_target is not None and exercise.slug == current_target.slug,
                'progress': {
                    'status': status,
                    'attempts_count': attempts_count,
                    'best_passed_tests': progress.best_passed_tests if progress else 0,
                    'best_total_tests': progress.best_total_tests if progress else 0,
                    'passed_once': passed_once,
                },
            }
        )

    remaining_exercises = max(0, summary['total'] - summary['completed'])
    milestone_unlocked = remaining_exercises <= 1 and summary['total'] > 0

    return 200, {
        'slug': track.slug,
        'name': track.name,
        'module_slug': track.module.slug if track.module else None,
        'module_name': track.module.name if track.module else None,
        'category_slug': track.category.slug,
        'category_name': track.category.name,
        'description': track.description,
        'goal': track.goal or track.description,
        'level_label': track.level_label or 'Trilha ativa',
        'progress_percent': summary['progress_percent'],
        'completed_exercises': summary['completed'],
        'total_exercises': summary['total'],
        'current_target_slug': current_target.slug if current_target else None,
        'current_target_title': current_target.title if current_target else None,
        'concept_kicker': track.concept_kicker or 'Conceitos trabalhados',
        'concepts': [
            {
                'title': concept.title,
                'summary': concept.summary,
                'why_it_matters': concept.why_it_matters,
                'common_mistake': concept.common_mistake,
            }
            for concept in track.concepts.all()
        ],
        'prerequisites': [prerequisite.label for prerequisite in track.prerequisites.all()],
        'exercises': exercises,
        'milestone': {
            'title': track.milestone_title or 'Checkpoint da trilha',
            'summary': track.milestone_summary or 'Marco especial de consolidação desta trilha.',
            'requirement_label': track.milestone_requirement_label or 'Concluir os módulos principais da trilha.',
            'unlocked': milestone_unlocked,
            'remaining_exercises': remaining_exercises,
        },
    }


def serialize_exercise_summary(exercise):
    meta = build_exercise_catalog_meta(exercise)
    return {
        'id': exercise.id,
        'slug': exercise.slug,
        'title': exercise.title,
        'learning_objectives': list(exercise.learning_objectives or []),
        'family_key': meta['family_key'],
        'difficulty': exercise.difficulty,
        'language': exercise.language,
        'professor_note': exercise.professor_note,
        'exercise_type': meta['exercise_type'],
        'exercise_type_label': meta['exercise_type_label'],
        'estimated_time_minutes': meta['estimated_time_minutes'],
        'concept_summary': meta['concept_summary'],
        'track_position': meta['track_position'],
        'module_slug': exercise.track.module.slug if exercise.track and exercise.track.module else None,
        'module_name': exercise.track.module.name if exercise.track and exercise.track.module else None,
        'category_slug': exercise.category.slug if exercise.category else None,
        'category_name': exercise.category.name if exercise.category else None,
        'track_slug': exercise.track.slug if exercise.track else None,
        'track_name': exercise.track.name if exercise.track else None,
    }


@router.get(
    '/tracks/{track_slug}/explanations/{exercise_slug}',
    response={200: ExerciseExplanationSchema, 401: ErrorSchema, 404: ErrorSchema},
    summary='Retorna a documentação técnica progressiva de um módulo específico da trilha.',
)
def get_track_explanation(request, track_slug: str, exercise_slug: str, authorization: str | None = Header(default=None)):
    try:
        require_session(authorization)
    except PermissionError as error:
        return 401, {'message': str(error)}

    track = get_track_by_slug(track_slug)
    if track is None:
        return 404, {'message': 'Trilha não encontrada.'}

    exercise = Exercise.objects.select_related('track').filter(slug=exercise_slug, track=track, is_active=True).first()
    if exercise is None:
        return 404, {'message': 'Módulo não encontrado para essa trilha.'}

    explanation = ensure_exercise_explanation(exercise)
    explanation = type(explanation).objects.prefetch_related('concepts', 'code_examples').get(pk=explanation.pk)
    objective_blueprint = (
        build_explanation_blueprint_for_exercise(exercise)
        if exercise.family_key == Exercise.FAMILY_OBJECTIVE_ITEM
        else None
    )
    meta = build_exercise_catalog_meta(exercise)

    return 200, {
        'module_slug': track.module.slug if track.module else None,
        'module_name': track.module.name if track.module else None,
        'track_slug': track.slug,
        'track_name': track.name,
        'track_goal': track.goal or track.description,
        'level_label': track.level_label or 'Trilha ativa',
        'exercise_slug': exercise.slug,
        'exercise_title': exercise.title,
        'exercise_type_label': meta['exercise_type_label'],
        'estimated_time_minutes': meta['estimated_time_minutes'],
        'concept_summary': meta['concept_summary'],
        'pedagogical_brief': meta['pedagogical_brief'],
        'learning_goal': objective_blueprint.learning_goal if objective_blueprint else explanation.learning_goal,
        'concept_focus_markdown': objective_blueprint.concept_focus_markdown if objective_blueprint else explanation.concept_focus_markdown,
        'reading_strategy_markdown': objective_blueprint.reading_strategy_markdown if objective_blueprint else explanation.reading_strategy_markdown,
        'implementation_strategy_markdown': objective_blueprint.implementation_strategy_markdown if objective_blueprint else explanation.implementation_strategy_markdown,
        'assessment_notes_markdown': objective_blueprint.assessment_notes_markdown if objective_blueprint else explanation.assessment_notes_markdown,
        'common_mistakes': list(objective_blueprint.common_mistakes if objective_blueprint else (explanation.common_mistakes or [])),
        'mastery_checklist': list(objective_blueprint.mastery_checklist if objective_blueprint else (explanation.mastery_checklist or [])),
        'prerequisites': [prerequisite.label for prerequisite in track.prerequisites.all()],
        'concepts': [
            {
                'title': concept.title,
                'explanation_text': concept.explanation_text,
                'why_it_matters': concept.why_it_matters,
                'common_mistake': concept.common_mistake,
            }
            for concept in (
                objective_blueprint.concepts
                if objective_blueprint
                else explanation.concepts.all()
            )
        ],
        'code_examples': [
            {
                'title': example.title,
                'rationale': example.rationale,
                'language': example.language,
                'code': example.code,
            }
            for example in (
                objective_blueprint.code_examples
                if objective_blueprint
                else explanation.code_examples.all()
            )
        ],
        **(
            _build_objective_explanation_payload(exercise)
            if exercise.family_key == Exercise.FAMILY_OBJECTIVE_ITEM
            else {
                'presentation_mode': 'default',
                'question_focus': '',
                'answer_rationale': '',
                'distractor_rationales': [],
            }
        ),
    }
