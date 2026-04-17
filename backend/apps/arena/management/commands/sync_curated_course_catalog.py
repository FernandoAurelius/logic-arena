import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.arena.models import (
    Exercise,
    ExerciseCategory,
    ExerciseTestCase,
    ExerciseTrack,
    ExerciseTrackConcept,
    ExerciseTrackPrerequisite,
    ExerciseType,
    LearningModule,
)
from apps.arena.schemas import ExerciseCreateSchema, TestCaseInputSchema
from apps.catalog.application.services import create_exercise


CATEGORY_DEFAULTS = {
    'slug': 'fundamentos-da-computacao',
    'name': 'Fundamentos da Computação',
    'description': 'História, arquitetura, informação e sistemas de informação em trilhas introdutórias.',
    'sort_order': 15,
}


EXERCISE_TYPE_DEFAULTS = [
    {
        'slug': 'revisao-objetiva',
        'name': 'Revisão objetiva',
        'description': 'Questões objetivas de revisão progressiva com foco conceitual.',
        'sort_order': 8,
    },
    {
        'slug': 'checkpoint-de-revisao',
        'name': 'Checkpoint de revisão',
        'description': 'Blocos objetivos de consolidação ao fim de cada trilha.',
        'sort_order': 9,
    },
    {
        'slug': 'simulado-final',
        'name': 'Simulado final',
        'description': 'Simulado objetivo em formato de revisão integrada.',
        'sort_order': 10,
    },
]


def _prefixed_slug(prefix: str, slug: str) -> str:
    return f'{prefix}-{slug}'


def _string_list(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, tuple):
        return [str(item).strip() for item in value if str(item).strip()]
    cleaned = str(value).strip()
    return [cleaned] if cleaned else []


def _render_statement(content_blocks: list[dict], fallback_title: str) -> str:
    sections: list[str] = []
    for block in content_blocks:
        if not isinstance(block, dict):
            continue
        title = str(block.get('title') or '').strip()
        content = str(block.get('content') or '').strip()
        if title and content:
            sections.append(f'{title}\n{content}')
        elif content:
            sections.append(content)
        elif title:
            sections.append(title)
    return '\n\n'.join(sections).strip() or fallback_title


def _module_name_from_course(course_payload: dict) -> str:
    title = str(course_payload.get('title') or '').strip()
    if ' - ' in title:
        return title.split(' - ', 1)[-1].strip()
    raw = str(course_payload.get('module') or '').strip()
    if raw:
        return raw.replace('-', ' ').title()
    return title or 'Curso curado'


def _module_description_from_course(course_payload: dict) -> str:
    subtitle = str(course_payload.get('subtitle') or '').strip()
    target_exam = str(course_payload.get('target_exam') or '').strip()
    source_materials = course_payload.get('source_materials') or []
    materials_summary = ', '.join(
        f"{item.get('title', 'material')} ({item.get('type', 'fonte')})"
        for item in source_materials
        if isinstance(item, dict)
    )
    parts = [
        str(course_payload.get('title') or '').strip(),
        subtitle,
        f'Avaliação-alvo: {target_exam}.' if target_exam else '',
        f'Materiais-base: {materials_summary}.' if materials_summary else '',
    ]
    return ' '.join(part for part in parts if part).strip()


def _build_track_concepts(module_payload: dict) -> list[dict]:
    concepts: list[dict] = []
    lessons = module_payload.get('lessons') or []
    for index, lesson in enumerate(lessons, start=1):
        instructional_text = lesson.get('instructional_text') or {}
        key_points = _string_list(instructional_text.get('key_points'))
        common_mistakes = _string_list(instructional_text.get('common_mistakes'))
        concepts.append(
            {
                'title': str(lesson.get('title') or f'Lição {index}').strip(),
                'summary': str(instructional_text.get('overview') or lesson.get('title') or '').strip(),
                'why_it_matters': key_points[0] if key_points else str(module_payload.get('summary') or '').strip(),
                'common_mistake': common_mistakes[0] if common_mistakes else '',
                'sort_order': index,
            }
        )
    return concepts


def _build_track_payload(course_payload: dict, module_payload: dict, *, category_slug: str, sort_order: int) -> dict:
    prefix = str(course_payload.get('track') or course_payload.get('slug') or 'curso').strip()
    checkpoint = module_payload.get('checkpoint') or {}
    return {
        'slug': _prefixed_slug(prefix, str(module_payload['slug']).strip()),
        'name': str(module_payload.get('title') or '').strip(),
        'description': str(module_payload.get('summary') or '').strip(),
        'goal': ' '.join(_string_list(module_payload.get('learning_objectives'))[:2]).strip()
        or str(module_payload.get('summary') or '').strip(),
        'level_label': str(course_payload.get('target_exam') or 'Revisão').strip(),
        'concept_kicker': str(course_payload.get('subtitle') or 'Revisão progressiva').strip(),
        'milestone_title': str(checkpoint.get('title') or f"Checkpoint - {module_payload.get('title', 'Trilha')}").strip(),
        'milestone_summary': str(checkpoint.get('summary') or module_payload.get('summary') or '').strip(),
        'milestone_requirement_label': 'Concluir os exercícios de revisão desta trilha.',
        'sort_order': sort_order,
        'category_slug': category_slug,
        'concepts': _build_track_concepts(module_payload),
        'prerequisites': [],
    }


def _build_final_review_track(course_payload: dict, *, category_slug: str, sort_order: int) -> dict:
    final_review = course_payload.get('final_review_exam') or {}
    prefix = str(course_payload.get('track') or course_payload.get('slug') or 'curso').strip()
    return {
        'slug': _prefixed_slug(prefix, str(final_review['slug']).strip()),
        'name': str(final_review.get('title') or '').strip(),
        'description': str(final_review.get('summary') or '').strip(),
        'goal': 'Consolidar os eixos principais da revisão em formato de simulado final.',
        'level_label': str(course_payload.get('target_exam') or 'Revisão').strip(),
        'concept_kicker': 'Simulado integrador',
        'milestone_title': str(final_review.get('title') or 'Simulado final').strip(),
        'milestone_summary': str(final_review.get('summary') or '').strip(),
        'milestone_requirement_label': 'Fechar o simulado completo com leitura cuidadosa das alternativas.',
        'sort_order': sort_order,
        'category_slug': category_slug,
        'concepts': [],
        'prerequisites': [],
    }


def _exercise_type_slug(*, is_checkpoint: bool = False, is_final_review: bool = False) -> str:
    if is_final_review:
        return 'simulado-final'
    if is_checkpoint:
        return 'checkpoint-de-revisao'
    return 'revisao-objetiva'


def _exercise_payload(
    course_payload: dict,
    track_payload: dict,
    exercise_definition: dict,
    *,
    track_position: int,
    pedagogical_brief: str,
    professor_note: str,
    exercise_type_slug: str,
) -> ExerciseCreateSchema:
    prefix = str(course_payload.get('track') or course_payload.get('slug') or 'curso').strip()
    content_blocks = list(exercise_definition.get('content_blocks') or [])
    learning_objectives = _string_list(exercise_definition.get('learning_objectives'))
    statement = _render_statement(content_blocks, str(exercise_definition.get('title') or '').strip())
    concept_summary = (
        learning_objectives[0]
        if learning_objectives
        else str(exercise_definition.get('title') or '').strip()
    )
    return ExerciseCreateSchema(
        slug=_prefixed_slug(prefix, str(exercise_definition['slug']).strip()),
        title=str(exercise_definition.get('title') or '').strip(),
        statement=statement,
        learning_objectives=learning_objectives,
        family_key=str(exercise_definition.get('family_key') or Exercise.FAMILY_OBJECTIVE_ITEM).strip(),
        difficulty=str(exercise_definition.get('difficulty') or 'intermediário').strip(),
        language='python',
        module_slug=str(course_payload['module']).strip(),
        module_name=_module_name_from_course(course_payload),
        module_description=_module_description_from_course(course_payload),
        module_audience=str(course_payload.get('audience') or '').strip(),
        module_source_kind='curso-curado',
        category_slug=track_payload['category_slug'],
        category_name=CATEGORY_DEFAULTS['name'],
        track_slug=track_payload['slug'],
        track_name=track_payload['name'],
        exercise_type_slug=exercise_type_slug,
        estimated_time_minutes=int(exercise_definition.get('estimated_time_minutes') or 15),
        version=1,
        content_blocks=content_blocks,
        workspace_spec=dict(exercise_definition.get('workspace_spec') or {}),
        evaluation_plan=dict(exercise_definition.get('evaluation_plan') or {}),
        review_profile=str(exercise_definition.get('review_profile') or 'objective_item_default').strip(),
        misconception_tags=_string_list(exercise_definition.get('misconception_tags')),
        progression_rules=dict(exercise_definition.get('progression_rules') or {}),
        track_position=track_position,
        concept_summary=concept_summary,
        pedagogical_brief=pedagogical_brief,
        professor_note=professor_note,
        test_cases=[],
    )


def _upsert_track(module: LearningModule, category: ExerciseCategory, track_payload: dict) -> tuple[ExerciseTrack, bool]:
    track, created = ExerciseTrack.objects.update_or_create(
        slug=track_payload['slug'],
        defaults={
            'module': module,
            'category': category,
            'name': track_payload['name'],
            'description': track_payload['description'],
            'goal': track_payload['goal'],
            'level_label': track_payload['level_label'],
            'concept_kicker': track_payload['concept_kicker'],
            'milestone_title': track_payload['milestone_title'],
            'milestone_summary': track_payload['milestone_summary'],
            'milestone_requirement_label': track_payload['milestone_requirement_label'],
            'sort_order': track_payload['sort_order'],
        },
    )
    ExerciseTrackConcept.objects.filter(track=track).delete()
    if track_payload['concepts']:
        ExerciseTrackConcept.objects.bulk_create(
            [
                ExerciseTrackConcept(
                    track=track,
                    title=concept['title'],
                    summary=concept['summary'],
                    why_it_matters=concept['why_it_matters'],
                    common_mistake=concept['common_mistake'],
                    sort_order=concept['sort_order'],
                )
                for concept in track_payload['concepts']
            ]
        )
    ExerciseTrackPrerequisite.objects.filter(track=track).delete()
    if track_payload['prerequisites']:
        ExerciseTrackPrerequisite.objects.bulk_create(
            [
                ExerciseTrackPrerequisite(
                    track=track,
                    label=prerequisite['label'],
                    sort_order=prerequisite['sort_order'],
                )
                for prerequisite in track_payload['prerequisites']
            ]
        )
    return track, created


def _upsert_exercise(payload: ExerciseCreateSchema) -> tuple[Exercise, bool]:
    exercise = Exercise.objects.filter(slug=payload.slug).first()
    if exercise is None:
        return create_exercise(payload), True

    category = ExerciseCategory.objects.filter(slug=payload.category_slug).first()
    track = ExerciseTrack.objects.filter(slug=payload.track_slug).first()
    exercise_type = ExerciseType.objects.filter(slug=payload.exercise_type_slug).first()
    exercise.title = payload.title
    exercise.statement = payload.statement
    exercise.learning_objectives = list(payload.learning_objectives or [])
    exercise.family_key = payload.family_key
    exercise.difficulty = payload.difficulty
    exercise.language = payload.language
    exercise.category = category or exercise.category
    exercise.track = track or exercise.track
    exercise.exercise_type = exercise_type or exercise.exercise_type
    exercise.estimated_time_minutes = payload.estimated_time_minutes
    exercise.version = payload.version
    exercise.content_blocks = list(payload.content_blocks or [])
    exercise.workspace_spec = dict(payload.workspace_spec or {})
    exercise.evaluation_plan = dict(payload.evaluation_plan or {})
    exercise.review_profile = payload.review_profile
    exercise.misconception_tags = list(payload.misconception_tags or [])
    exercise.progression_rules = dict(payload.progression_rules or {})
    exercise.track_position = payload.track_position
    exercise.concept_summary = payload.concept_summary
    exercise.pedagogical_brief = payload.pedagogical_brief
    exercise.starter_code = payload.starter_code
    exercise.sample_input = payload.sample_input
    exercise.sample_output = payload.sample_output
    exercise.professor_note = payload.professor_note
    exercise.save()

    ExerciseTestCase.objects.filter(exercise=exercise).delete()
    if payload.test_cases:
        ExerciseTestCase.objects.bulk_create(
            [
                ExerciseTestCase(
                    exercise=exercise,
                    input_data=test_case.input_data,
                    expected_output=test_case.expected_output,
                    is_hidden=test_case.is_hidden,
                )
                for test_case in payload.test_cases
            ]
        )

    from apps.arena.services import sync_exercise_explanation

    sync_exercise_explanation(exercise)
    return exercise, False


class Command(BaseCommand):
    help = 'Sincroniza um curso curado em JSON para módulo, trilhas e exercícios do catálogo.'

    def add_arguments(self, parser):
        parser.add_argument('--source', required=True, help='Caminho absoluto do JSON curado do curso.')
        parser.add_argument(
            '--replace',
            action='store_true',
            help='Remove exercícios e trilhas já ingeridos para o mesmo prefixo antes de recriar.',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        source_path = Path(options['source']).expanduser()
        if not source_path.exists():
            raise CommandError(f'Arquivo não encontrado: {source_path}')

        try:
            payload = json.loads(source_path.read_text())
        except json.JSONDecodeError as error:
            raise CommandError(f'JSON inválido em {source_path}: {error}') from error

        course_payload = payload.get('course')
        if not isinstance(course_payload, dict):
            raise CommandError('O JSON precisa conter a chave raiz "course".')

        required_fields = ['slug', 'title', 'module', 'track']
        missing_fields = [field for field in required_fields if not str(course_payload.get(field) or '').strip()]
        if missing_fields:
            raise CommandError(f'Campos obrigatórios ausentes no curso: {", ".join(missing_fields)}')

        module, _ = LearningModule.objects.update_or_create(
            slug=str(course_payload['module']).strip(),
            defaults={
                'name': _module_name_from_course(course_payload),
                'description': _module_description_from_course(course_payload),
                'audience': str(course_payload.get('audience') or '').strip(),
                'source_kind': 'curso-curado',
                'status': LearningModule.STATUS_ACTIVE,
                'sort_order': 6,
            },
        )

        category, _ = ExerciseCategory.objects.update_or_create(
            slug=CATEGORY_DEFAULTS['slug'],
            defaults={
                'name': CATEGORY_DEFAULTS['name'],
                'description': CATEGORY_DEFAULTS['description'],
                'sort_order': CATEGORY_DEFAULTS['sort_order'],
            },
        )

        for exercise_type_defaults in EXERCISE_TYPE_DEFAULTS:
            ExerciseType.objects.update_or_create(
                slug=exercise_type_defaults['slug'],
                defaults={
                    'name': exercise_type_defaults['name'],
                    'description': exercise_type_defaults['description'],
                    'sort_order': exercise_type_defaults['sort_order'],
                },
            )

        prefix = str(course_payload['track']).strip()
        incoming_track_slugs: set[str] = set()
        incoming_exercise_slugs: set[str] = set()

        if options['replace']:
            Exercise.objects.filter(slug__startswith=f'{prefix}-').delete()
            ExerciseTrack.objects.filter(slug__startswith=f'{prefix}-').delete()

        created_tracks = 0
        created_exercises = 0
        total_exercises = 0

        modules = course_payload.get('modules') or []
        for track_index, module_payload in enumerate(modules, start=1):
            track_payload = _build_track_payload(
                course_payload,
                module_payload,
                category_slug=category.slug,
                sort_order=track_index,
            )
            incoming_track_slugs.add(track_payload['slug'])
            _track, created = _upsert_track(module, category, track_payload)
            created_tracks += int(created)

            track_position = 1
            for lesson in module_payload.get('lessons') or []:
                lesson_overview = str((lesson.get('instructional_text') or {}).get('overview') or module_payload.get('summary') or '').strip()
                lesson_exam_tips = _string_list((lesson.get('instructional_text') or {}).get('exam_tips'))
                professor_note = lesson_exam_tips[0] if lesson_exam_tips else str(module_payload.get('summary') or '').strip()
                for exercise_definition in lesson.get('exercise_definitions') or []:
                    exercise_payload = _exercise_payload(
                        course_payload,
                        track_payload,
                        exercise_definition,
                        track_position=track_position,
                        pedagogical_brief=lesson_overview,
                        professor_note=professor_note,
                        exercise_type_slug=_exercise_type_slug(),
                    )
                    incoming_exercise_slugs.add(exercise_payload.slug)
                    _exercise, created = _upsert_exercise(exercise_payload)
                    created_exercises += int(created)
                    total_exercises += 1
                    track_position += 1

            checkpoint = module_payload.get('checkpoint') or {}
            checkpoint_brief = str(checkpoint.get('summary') or module_payload.get('summary') or '').strip()
            checkpoint_note = str(checkpoint.get('title') or module_payload.get('title') or '').strip()
            for exercise_definition in checkpoint.get('exercise_definitions') or []:
                exercise_payload = _exercise_payload(
                    course_payload,
                    track_payload,
                    exercise_definition,
                    track_position=track_position,
                    pedagogical_brief=checkpoint_brief,
                    professor_note=checkpoint_note,
                    exercise_type_slug=_exercise_type_slug(is_checkpoint=True),
                )
                incoming_exercise_slugs.add(exercise_payload.slug)
                _exercise, created = _upsert_exercise(exercise_payload)
                created_exercises += int(created)
                total_exercises += 1
                track_position += 1

        final_review = course_payload.get('final_review_exam')
        if isinstance(final_review, dict) and str(final_review.get('slug') or '').strip():
            final_track_payload = _build_final_review_track(
                course_payload,
                category_slug=category.slug,
                sort_order=len(modules) + 1,
            )
            incoming_track_slugs.add(final_track_payload['slug'])
            _track, created = _upsert_track(module, category, final_track_payload)
            created_tracks += int(created)

            for track_position, exercise_definition in enumerate(final_review.get('exercise_definitions') or [], start=1):
                exercise_payload = _exercise_payload(
                    course_payload,
                    final_track_payload,
                    exercise_definition,
                    track_position=track_position,
                    pedagogical_brief=str(final_review.get('summary') or '').strip(),
                    professor_note=str(final_review.get('title') or '').strip(),
                    exercise_type_slug=_exercise_type_slug(is_final_review=True),
                )
                incoming_exercise_slugs.add(exercise_payload.slug)
                _exercise, created = _upsert_exercise(exercise_payload)
                created_exercises += int(created)
                total_exercises += 1

        stale_exercises = Exercise.objects.filter(slug__startswith=f'{prefix}-').exclude(slug__in=incoming_exercise_slugs)
        if stale_exercises.exists():
            stale_exercises.delete()

        stale_tracks = ExerciseTrack.objects.filter(slug__startswith=f'{prefix}-').exclude(slug__in=incoming_track_slugs)
        if stale_tracks.exists():
            stale_tracks.delete()

        self.stdout.write(
            self.style.SUCCESS(
                f'Curso "{course_payload["title"]}" sincronizado: '
                f'{len(incoming_track_slugs)} trilhas ({created_tracks} novas) e '
                f'{total_exercises} exercícios ({created_exercises} novos).'
            )
        )
