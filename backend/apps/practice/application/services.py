import json
from dataclasses import dataclass
from urllib.error import URLError
from urllib.request import Request, urlopen

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.arena.models import (
    AIReview,
    ArenaUser,
    AssessmentContainer,
    AssessmentContainerPart,
    AttemptSession,
    EvaluationRun,
    ExerciseDefinition,
    Submission,
    SubmissionSnapshot,
    UserExerciseProgress,
)
from apps.practice.application.registry import OBJECTIVE_SNIPPET_TEMPLATES, get_family_spec, resolve_surface_key
from apps.practice.domain import (
    build_objective_option_catalog,
    evaluate_objective_selection,
    format_execution_results_console,
    normalize_objective_template_key,
    normalize_text,
    outputs_match_robust,
)
from apps.progress.application.services import apply_submission_progress, build_exercise_progress_payload, build_user_progress_summary
from apps.review.application.services import schedule_submission_feedback


DEFAULT_EXERCISE_TYPE_SLUG = 'drill-de-implementacao'
DEFAULT_EXERCISE_TYPE_LABEL = 'Drill de implementação'
DEFAULT_OBJECTIVE_ITEM_XP = 35


def _resolve_objective_choice_mode(template_key: str, evaluation_plan: dict, correct_options: list[object], workspace_spec: dict | None = None) -> str:
    workspace_spec = workspace_spec or {}
    choice_mode = str(
        workspace_spec.get('choice_mode')
        or evaluation_plan.get('choice_mode')
        or evaluation_plan.get('selection_mode')
        or ('multiple' if template_key == 'multi-select' or len(correct_options) > 1 else 'single')
    ).strip().lower()
    if choice_mode not in {'single', 'multiple'}:
        return 'single'
    return choice_mode


def _build_objective_template_meta(
    exercise: ExerciseDefinition,
    *,
    template_key: str,
    choice_mode: str,
    option_catalog: list[dict],
    snippet_block: dict | None,
) -> dict:
    template_titles = {
        'single-choice': 'Escolha objetiva',
        'multi-select': 'Seleção de afirmações',
        'snippet-read-only': 'Leitura de snippet',
        'compile-runtime-output': 'Compile / Runtime / Output',
        'behavior-classification': 'Behavior classification',
        'output-prediction': 'Previsão de saída',
    }
    analysis_steps = {
        'single-choice': [
            'Leia o estímulo até localizar a regra que decide a alternativa correta.',
            'Compare a alternativa escolhida com os distratores mais plausíveis.',
        ],
        'multi-select': [
            'Avalie cada afirmação separadamente antes de concluir o conjunto final.',
            'Procure omissões e falsos positivos, não só a primeira impressão.',
        ],
        'snippet-read-only': [
            'Leia o snippet como evidência, sem reescrever mentalmente o código.',
            'Valide escopo, tipos e fluxo antes de decidir.',
        ],
        'compile-runtime-output': [
            'Decida primeiro se o código compila.',
            'Se compilar, separe falha em runtime de saída observável.',
            'Só preencha a saída quando o veredito correto for output.',
        ],
        'behavior-classification': [
            'Observe o comportamento real do trecho, não só a intenção aparente.',
            'Considere dispatch, efeitos colaterais e ordem de execução.',
        ],
        'output-prediction': [
            'Simule a execução linha a linha antes de escolher a saída.',
            'Confirme ordem, espaçamento e valores finais do output.',
        ],
    }
    response_shape = {
        'single-choice': 'single_choice',
        'multi-select': 'multi_select',
        'snippet-read-only': 'single_choice',
        'compile-runtime-output': 'classifier_with_optional_output',
        'behavior-classification': 'single_choice',
        'output-prediction': 'single_choice',
    }
    evaluation_plan = exercise.evaluation_plan or {}
    expected_output_text = normalize_text(
        evaluation_plan.get('expected_output_text')
        or evaluation_plan.get('expected_output')
        or evaluation_plan.get('correct_output_text')
        or evaluation_plan.get('output_text')
        or ''
    )
    requires_output_text = template_key == 'compile-runtime-output' and bool(expected_output_text)

    return {
        'key': template_key,
        'title': template_titles.get(template_key, 'Template objetivo'),
        'stimulus_kind': 'snippet' if snippet_block is not None else 'statement',
        'choice_mode': choice_mode,
        'response_shape': response_shape.get(template_key, 'single_choice'),
        'requires_output_text': requires_output_text,
        'response_input_label': 'Saída esperada' if requires_output_text else '',
        'response_input_placeholder': 'INSIRA A SAÍDA ESPERADA...' if requires_output_text else '',
        'analysis_steps': analysis_steps.get(template_key, []),
        'verdict_options': [
            {
                'key': option['canonical_key'],
                'label': option['label'],
            }
            for option in option_catalog
        ],
    }


def _build_objective_workspace_spec(exercise: ExerciseDefinition) -> dict:
    family_spec = get_family_spec(exercise.family_key)
    evaluation_plan = exercise.evaluation_plan or {}
    base_workspace_spec = dict(exercise.workspace_spec or {})
    option_catalog = build_objective_option_catalog(evaluation_plan, exercise.content_blocks or [])
    correct_options = evaluation_plan.get('correct_options') or evaluation_plan.get('correct_answers') or evaluation_plan.get('correct_answer') or evaluation_plan.get('answer_key') or []
    if not isinstance(correct_options, (list, tuple, set)):
        correct_options = [correct_options]
    snippet_block = _extract_objective_snippet_block(exercise)
    snippet_code = base_workspace_spec.get('snippet')
    if snippet_block is None and snippet_code not in (None, ''):
        snippet_block = {
            'kind': 'snippet',
            'title': base_workspace_spec.get('snippet_title') or base_workspace_spec.get('snippet_filename') or 'Trecho de código',
            'language': base_workspace_spec.get('snippet_language') or exercise.language or 'python',
            'read_only': bool(base_workspace_spec.get('snippet_read_only', True)),
            'code': str(snippet_code),
        }

    template_key = normalize_objective_template_key(
        base_workspace_spec.get('template')
        or evaluation_plan.get('template')
        or evaluation_plan.get('kind')
        or 'single-choice'
    )
    choice_mode = _resolve_objective_choice_mode(template_key, evaluation_plan, list(correct_options), base_workspace_spec)
    template_meta = _build_objective_template_meta(
        exercise,
        template_key=template_key,
        choice_mode=choice_mode,
        option_catalog=option_catalog,
        snippet_block=snippet_block,
    )

    return {
        **base_workspace_spec,
        'surface_key': base_workspace_spec.get('surface_key') or family_spec.default_surface_key,
        'workspace_kind': base_workspace_spec.get('workspace_kind') or 'objective_form',
        'stimulus_kind': base_workspace_spec.get('stimulus_kind') or ('snippet' if snippet_block is not None else 'statement'),
        'choice_mode': choice_mode,
        'template': template_key,
        'template_meta': template_meta,
        'snippet': base_workspace_spec.get('snippet', snippet_block['code'] if snippet_block is not None else ''),
        'snippet_language': base_workspace_spec.get('snippet_language', snippet_block['language'] if snippet_block is not None else exercise.language),
        'snippet_read_only': base_workspace_spec.get('snippet_read_only', bool(snippet_block)),
        'options': base_workspace_spec.get('options') or option_catalog,
        'selected_options': list(base_workspace_spec.get('selected_options') or []),
        'response_text': str(base_workspace_spec.get('response_text') or ''),
        'allow_multiple': bool(base_workspace_spec.get('allow_multiple')) or choice_mode == 'multiple',
    }


def _extract_objective_snippet_block(exercise: ExerciseDefinition) -> dict | None:
    evaluation_plan = exercise.evaluation_plan or {}
    template = normalize_objective_template_key(evaluation_plan.get('template') or evaluation_plan.get('kind') or '')
    snippet = (
        evaluation_plan.get('snippet')
        or evaluation_plan.get('snippet_code')
        or evaluation_plan.get('read_only_snippet')
        or evaluation_plan.get('code')
    )
    if not snippet and template not in OBJECTIVE_SNIPPET_TEMPLATES:
        return None
    if not snippet:
        return None

    snippet_language = (
        evaluation_plan.get('snippet_language')
        or evaluation_plan.get('language')
        or exercise.language
        or 'python'
    )
    return {
        'kind': 'snippet',
        'title': evaluation_plan.get('snippet_title') or 'Trecho de código',
        'language': snippet_language,
        'read_only': True,
        'code': str(snippet),
    }


def build_default_content_blocks(exercise: ExerciseDefinition) -> list[dict]:
    if exercise.content_blocks:
        return list(exercise.content_blocks)
    if exercise.family_key == ExerciseDefinition.FAMILY_OBJECTIVE_ITEM:
        evaluation_plan = exercise.evaluation_plan or {}
        option_catalog = build_objective_option_catalog(evaluation_plan, exercise.content_blocks or [])
        correct_options = evaluation_plan.get('correct_options') or evaluation_plan.get('correct_answers') or evaluation_plan.get('correct_answer') or evaluation_plan.get('answer_key') or []
        if not isinstance(correct_options, (list, tuple, set)):
            correct_options = [correct_options]
        template_key = normalize_objective_template_key(evaluation_plan.get('template') or evaluation_plan.get('kind') or 'single-choice')
        choice_mode = _resolve_objective_choice_mode(template_key, evaluation_plan, list(correct_options))
        blocks = [
            {
                'kind': 'statement',
                'title': exercise.title,
                'content': exercise.statement,
            }
        ]
        snippet_block = _extract_objective_snippet_block(exercise)
        if snippet_block is not None:
            blocks.append(snippet_block)
        if option_catalog:
            blocks.append(
                {
                    'kind': 'objective-options',
                    'choice_mode': choice_mode,
                    'options': option_catalog,
                }
            )
        return blocks
    return [
        {
            'kind': 'statement',
            'title': exercise.title,
            'content': exercise.statement,
        }
    ]


def build_default_workspace_spec(exercise: ExerciseDefinition) -> dict:
    if exercise.workspace_spec and exercise.family_key != ExerciseDefinition.FAMILY_OBJECTIVE_ITEM:
        return dict(exercise.workspace_spec)

    if exercise.family_key == ExerciseDefinition.FAMILY_OBJECTIVE_ITEM:
        return _build_objective_workspace_spec(exercise)

    family_spec = get_family_spec(exercise.family_key)
    if exercise.family_key == ExerciseDefinition.FAMILY_CODE_LAB:
        file_name = 'main.py' if exercise.language == 'python' else f'main.{exercise.language}'
        return {
            'surface_key': family_spec.default_surface_key,
            'workspace_kind': 'single_file',
            'language': exercise.language,
            'entrypoint': file_name,
            'files': {
                file_name: exercise.starter_code,
            },
        }

    return {
        'surface_key': family_spec.default_surface_key,
        'workspace_kind': 'form',
    }


def build_default_evaluation_plan(exercise: ExerciseDefinition) -> dict:
    if exercise.evaluation_plan:
        return dict(exercise.evaluation_plan)

    if exercise.family_key == ExerciseDefinition.FAMILY_CODE_LAB:
        return {
            'mechanism': 'runner_tests',
            'language': exercise.language,
            'template': 'implementation',
        }

    if exercise.family_key == ExerciseDefinition.FAMILY_OBJECTIVE_ITEM:
        return {
            'mechanism': 'objective_key',
            'template': 'single-choice',
            'choice_mode': 'single',
        }

    if exercise.family_key == ExerciseDefinition.FAMILY_RESTRICTED_CODE:
        return {
            'mechanism': 'structural_checker',
            'template': 'fix-the-snippet',
        }

    if exercise.family_key == ExerciseDefinition.FAMILY_CONTRACT_BEHAVIOR_LAB:
        return {
            'mechanism': 'contract_verifier',
            'template': 'http-contract',
        }

    return {
        'mechanism': 'rubric',
        'template': 'guided-response',
    }


def build_exercise_catalog_meta(exercise: ExerciseDefinition) -> dict:
    exercise_type = exercise.exercise_type.slug if exercise.exercise_type else DEFAULT_EXERCISE_TYPE_SLUG
    return {
        'exercise_type': exercise_type,
        'exercise_type_label': exercise.exercise_type.name if exercise.exercise_type else DEFAULT_EXERCISE_TYPE_LABEL,
        'estimated_time_minutes': exercise.estimated_time_minutes or 15,
        'concept_summary': exercise.concept_summary or exercise.professor_note,
        'pedagogical_brief': exercise.pedagogical_brief or exercise.professor_note,
        'track_position': exercise.track_position or 0,
        'family_key': exercise.family_key or ExerciseDefinition.FAMILY_CODE_LAB,
    }


def serialize_exercise_summary(exercise: ExerciseDefinition) -> dict:
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


def serialize_exercise_detail(exercise: ExerciseDefinition) -> dict:
    return {
        **serialize_exercise_summary(exercise),
        'statement': exercise.statement,
        'version': exercise.version,
        'content_blocks': build_default_content_blocks(exercise),
        'workspace_spec': build_default_workspace_spec(exercise),
        'evaluation_plan': build_default_evaluation_plan(exercise),
        'review_profile': exercise.review_profile,
        'misconception_tags': list(exercise.misconception_tags or []),
        'progression_rules': dict(exercise.progression_rules or {}),
        'starter_code': exercise.starter_code,
        'sample_input': exercise.sample_input,
        'sample_output': exercise.sample_output,
        'test_cases': list(exercise.test_cases.filter(is_hidden=False)),
    }


def serialize_submission_summary(submission: Submission) -> dict:
    return {
        'id': submission.id,
        'exercise_slug': submission.exercise.slug,
        'exercise_title': submission.exercise.title,
        'status': submission.status,
        'passed_tests': submission.passed_tests,
        'total_tests': submission.total_tests,
        'feedback_status': submission.feedback_status,
        'feedback_source': submission.feedback_source,
        'created_at': submission.created_at,
    }


def serialize_submission(submission: Submission) -> dict:
    progress = UserExerciseProgress.objects.filter(user=submission.user, exercise=submission.exercise).first()
    return {
        'id': submission.id,
        'status': submission.status,
        'passed_tests': submission.passed_tests,
        'total_tests': submission.total_tests,
        'source_code': submission.source_code,
        'console_output': submission.console_output,
        'feedback': submission.feedback,
        'feedback_status': submission.feedback_status,
        'feedback_source': submission.feedback_source,
        'feedback_payload': submission.feedback_payload,
        'review_chat_history': submission.review_chat_history,
        'created_at': submission.created_at,
        'results': submission.execution_results,
        'xp_awarded': submission.xp_awarded,
        'unlocked_progress_rewards': submission.unlocked_progress_rewards,
        'exercise_progress': build_exercise_progress_payload(progress)
        if progress
        else {
            'attempts_count': 0,
            'best_passed_tests': 0,
            'best_total_tests': 0,
            'best_ratio': 0,
            'xp_awarded_total': 0,
            'first_passed_at': None,
            'awarded_progress_markers': [],
        },
        'user_progress': build_user_progress_summary(submission.user),
    }


def serialize_attempt_session(session: AttemptSession) -> dict:
    latest_snapshot = session.snapshots.order_by('-created_at', '-id').select_related('legacy_submission').first()
    latest_evaluation = None
    latest_review = None
    if latest_snapshot is not None:
        latest_evaluation = latest_snapshot.evaluation_runs.order_by('-created_at', '-id').first()
        if latest_evaluation is not None:
            latest_review = getattr(latest_evaluation, 'ai_review', None)

    exercise = session.exercise
    assessment = session.assessment
    family_key = exercise.family_key if exercise else None
    surface_key = None
    if exercise is not None:
        surface_key = resolve_surface_key(exercise)
    elif isinstance(session.state, dict):
        surface_key = session.state.get('surface_key')

    serialized_progress = None
    if exercise is not None:
        progress = UserExerciseProgress.objects.filter(user=session.user, exercise=exercise).first()
        if progress is not None:
            unlocked_rewards = []
            if 'passed_once' in (progress.awarded_progress_markers or []):
                unlocked_rewards.append(
                    {
                        'milestone_key': 'passed_once',
                        'label': 'Primeira aprovação',
                        'xp_awarded': DEFAULT_OBJECTIVE_ITEM_XP,
                    }
                )
            serialized_progress = {
                'xp_awarded': progress.xp_awarded_total,
                'unlocked_progress_rewards': unlocked_rewards,
                'exercise_progress': build_exercise_progress_payload(progress),
                'user_progress': build_user_progress_summary(session.user),
            }
    if serialized_progress is None and latest_snapshot is not None and latest_snapshot.legacy_submission is not None:
        serialized_progress = serialize_submission(latest_snapshot.legacy_submission)

    return {
        'id': session.id,
        'target_type': session.target_type,
        'exercise_slug': exercise.slug if exercise else None,
        'exercise_title': exercise.title if exercise else None,
        'assessment_slug': assessment.slug if assessment else None,
        'assessment_title': assessment.title if assessment else None,
        'family_key': family_key,
        'surface_key': surface_key,
        'mode': session.mode,
        'state': session.state or {},
        'current_workspace_state': session.current_workspace_state or {},
        'answer_state': session.answer_state or {},
        'attempt_status': session.attempt_status,
        'latest_snapshot': serialize_submission_snapshot(latest_snapshot) if latest_snapshot else None,
        'latest_evaluation': serialize_evaluation_run(latest_evaluation) if latest_evaluation else None,
        'latest_review': serialize_ai_review(latest_review) if latest_review else None,
        'xp_awarded': serialized_progress['xp_awarded'] if serialized_progress else 0,
        'unlocked_progress_rewards': serialized_progress['unlocked_progress_rewards'] if serialized_progress else [],
        'exercise_progress': serialized_progress['exercise_progress'] if serialized_progress else None,
        'user_progress': serialized_progress['user_progress'] if serialized_progress else None,
        'created_at': session.created_at,
        'updated_at': session.updated_at,
    }


def serialize_submission_snapshot(snapshot: SubmissionSnapshot) -> dict:
    return {
        'id': snapshot.id,
        'session_id': snapshot.session_id,
        'type': snapshot.type,
        'payload': snapshot.payload or {},
        'files': snapshot.files or {},
        'selected_options': list(snapshot.selected_options or []),
        'created_at': snapshot.created_at,
    }


def serialize_evaluation_run(evaluation_run: EvaluationRun) -> dict:
    return {
        'id': evaluation_run.id,
        'submission_snapshot_id': evaluation_run.submission_id,
        'normalized_score': evaluation_run.normalized_score,
        'verdict': evaluation_run.verdict,
        'evaluator_results': evaluation_run.evaluator_results or {},
        'evidence_bundle': evaluation_run.evidence_bundle or {},
        'misconception_inference': list(evaluation_run.misconception_inference or []),
        'raw_artifacts': evaluation_run.raw_artifacts or {},
        'created_at': evaluation_run.created_at,
    }


def serialize_ai_review(review: AIReview) -> dict:
    return {
        'id': review.id,
        'evaluation_run_id': review.evaluation_run_id,
        'profile_key': review.profile_key,
        'explanation': review.explanation,
        'next_steps': list(review.next_steps or []),
        'conversation_thread': list(review.conversation_thread or []),
        'created_at': review.created_at,
        'updated_at': review.updated_at,
    }


def serialize_assessment_container_part(part: AssessmentContainerPart) -> dict:
    return {
        'id': part.id,
        'title': part.title,
        'sort_order': part.sort_order,
        'exercise_slug': part.exercise.slug if part.exercise else None,
        'scoring_rules': part.scoring_rules or {},
        'timing_rules': part.timing_rules or {},
        'reveal_rules': part.reveal_rules or {},
    }


def serialize_assessment_container(container: AssessmentContainer) -> dict:
    return {
        'id': container.id,
        'slug': container.slug,
        'title': container.title,
        'mode': container.mode,
        'scoring_rules': container.scoring_rules or {},
        'timing_rules': container.timing_rules or {},
        'reveal_rules': container.reveal_rules or {},
        'parts': [serialize_assessment_container_part(part) for part in container.parts.all()],
    }


def build_session_config(exercise: ExerciseDefinition, mode: str = AttemptSession.MODE_PRACTICE) -> dict:
    surface_key = resolve_surface_key(exercise)
    return {
        'exercise': serialize_exercise_detail(exercise),
        'family_key': exercise.family_key,
        'surface_key': surface_key,
        'mode': mode,
        'workspace_spec': build_default_workspace_spec(exercise),
        'review_profile': exercise.review_profile,
    }


def create_attempt_session_for_exercise(user: ArenaUser, exercise: ExerciseDefinition, mode: str = AttemptSession.MODE_PRACTICE) -> AttemptSession:
    workspace_spec = build_default_workspace_spec(exercise)
    if exercise.family_key == ExerciseDefinition.FAMILY_OBJECTIVE_ITEM:
        evaluation_plan = build_default_evaluation_plan(exercise)
        template_key = normalize_objective_template_key(evaluation_plan.get('template', 'single-choice'))
        answer_state = {
            'selected_options': [],
            'selected_labels': [],
            'response_text': '',
            'template': template_key,
            'choice_mode': evaluation_plan.get('choice_mode', 'single'),
        }
    elif exercise.family_key == ExerciseDefinition.FAMILY_CODE_LAB:
        answer_state = {'source_code': exercise.starter_code}
    else:
        answer_state = {}

    return AttemptSession.objects.create(
        user=user,
        target_type=AttemptSession.TARGET_EXERCISE,
        exercise=exercise,
        mode=mode,
        state={'family_key': exercise.family_key, 'surface_key': resolve_surface_key(exercise)},
        current_workspace_state=workspace_spec,
        answer_state=answer_state,
    )


def create_attempt_session_for_assessment(user: ArenaUser, assessment: AssessmentContainer) -> AttemptSession:
    return AttemptSession.objects.create(
        user=user,
        target_type=AttemptSession.TARGET_ASSESSMENT,
        assessment=assessment,
        mode=assessment.mode,
        state={
            'assessment_slug': assessment.slug,
            'part_ids': list(assessment.parts.order_by('sort_order', 'id').values_list('id', flat=True)),
        },
        current_workspace_state={},
        answer_state={},
    )


def update_attempt_session_state(
    session: AttemptSession,
    state: dict | None = None,
    current_workspace_state: dict | None = None,
    answer_state: dict | None = None,
) -> AttemptSession:
    if state is not None:
        session.state = state
    if current_workspace_state is not None:
        session.current_workspace_state = current_workspace_state
    if answer_state is not None:
        session.answer_state = answer_state
    session.save(update_fields=['state', 'current_workspace_state', 'answer_state', 'updated_at'])
    return session


@dataclass
class ExecutionResult:
    ok: bool
    stdout: str
    stderr: str


def run_python(source_code: str, stdin: str) -> ExecutionResult:
    payload = json.dumps(
        {
            'language': 'python',
            'source_code': source_code,
            'stdin': stdin,
            'timeout_seconds': 5,
        }
    ).encode()
    request = Request(
        f'{settings.RUNNER_URL}/execute/python',
        data=payload,
        headers={'Content-Type': 'application/json'},
        method='POST',
    )

    try:
        with urlopen(request, timeout=8) as response:
            parsed = json.loads(response.read().decode())
            return ExecutionResult(
                ok=bool(parsed.get('ok')),
                stdout=str(parsed.get('stdout', '')),
                stderr=str(parsed.get('stderr', '')),
            )
    except URLError as error:
        return ExecutionResult(ok=False, stdout='', stderr=f'Runner indisponível: {error}')
    except Exception as error:  # pragma: no cover
        return ExecutionResult(ok=False, stdout='', stderr=str(error))


def execute_code_lab(exercise: ExerciseDefinition, source_code: str) -> tuple[list[dict], int, int, str, str]:
    results: list[dict] = []

    for index, test_case in enumerate(exercise.test_cases.all(), start=1):
        execution = run_python(source_code, test_case.input_data)
        actual_output = normalize_text(execution.stdout)
        expected_output = normalize_text(test_case.expected_output)
        passed = execution.ok and outputs_match_robust(expected_output, actual_output)
        results.append(
            {
                'index': index,
                'input_data': test_case.input_data,
                'expected_output': expected_output,
                'actual_output': actual_output,
                'passed': passed,
                'stderr': normalize_text(execution.stderr),
            }
        )

    passed_tests = sum(1 for result in results if result['passed'])
    total_tests = len(results)
    status = Submission.STATUS_PASSED if total_tests > 0 and passed_tests == total_tests else Submission.STATUS_FAILED
    console_output = format_execution_results_console(results)
    return results, passed_tests, total_tests, status, console_output


def create_legacy_submission(
    user: ArenaUser,
    exercise: ExerciseDefinition,
    source_code: str,
    results: list[dict],
    passed_tests: int,
    total_tests: int,
    status: str,
    console_output: str,
) -> Submission:
    submission = Submission.objects.create(
        user=user,
        exercise=exercise,
        source_code=source_code,
        status=status,
        passed_tests=passed_tests,
        total_tests=total_tests,
        console_output=console_output,
        feedback='Revisão com IA em processamento...',
        feedback_status=Submission.FEEDBACK_PENDING,
        feedback_source='agno-gemini',
        feedback_payload={
            'summary': 'Revisão com IA em processamento...',
            'strengths': [],
            'issues': [],
            'next_steps': [],
            'source': 'agno-gemini',
        },
        execution_results=results,
        review_chat_history=[],
        xp_awarded=0,
        unlocked_progress_rewards=[],
    )
    apply_submission_progress(user, exercise, submission)
    return submission


def build_code_lab_evaluation(
    session: AttemptSession,
    source_code: str,
    snapshot_type: str,
) -> tuple[SubmissionSnapshot, EvaluationRun, Submission | None]:
    exercise = session.exercise
    if exercise is None:
        raise ValueError('Sessão sem exercício associado.')

    results, passed_tests, total_tests, status, console_output = execute_code_lab(exercise, source_code)
    normalized_score = (passed_tests / total_tests) if total_tests else 0
    verdict = EvaluationRun.VERDICT_PASSED if status == Submission.STATUS_PASSED else EvaluationRun.VERDICT_FAILED
    legacy_submission = None

    if snapshot_type == SubmissionSnapshot.TYPE_SUBMIT:
        legacy_submission = create_legacy_submission(
            user=session.user,
            exercise=exercise,
            source_code=source_code,
            results=results,
            passed_tests=passed_tests,
            total_tests=total_tests,
            status=status,
            console_output=console_output,
        )

    snapshot = SubmissionSnapshot.objects.create(
        session=session,
        type=snapshot_type,
        payload={'source_code': source_code},
        files=(session.current_workspace_state or {}).get('files', {}),
        selected_options=[],
        legacy_submission=legacy_submission,
    )
    evaluation_run = EvaluationRun.objects.create(
        submission=snapshot,
        evaluator_results={
            'family_key': exercise.family_key,
            'mechanism': 'runner_tests',
            'passed_tests': passed_tests,
            'total_tests': total_tests,
        },
        normalized_score=normalized_score,
        verdict=verdict,
        evidence_bundle={
            'console_output': console_output,
            'results': results,
        },
        misconception_inference=[],
        raw_artifacts={
            'status': status,
            'source_code': source_code,
        },
        legacy_submission=legacy_submission,
    )

    if legacy_submission is not None:
        AIReview.objects.create(
            evaluation_run=evaluation_run,
            profile_key=exercise.review_profile,
            explanation='Revisão com IA em processamento...',
            next_steps=[],
            conversation_thread=[],
        )
        schedule_submission_feedback(
            legacy_submission.id,
            exercise.title,
            exercise.statement,
            source_code,
            passed_tests,
            total_tests,
            results,
            evaluation_run_id=evaluation_run.id,
        )

    session.answer_state = {'source_code': source_code}
    session.current_workspace_state = {
        **(session.current_workspace_state or {}),
        'files': {
            **((session.current_workspace_state or {}).get('files') or {}),
            ((session.current_workspace_state or {}).get('entrypoint') or 'main.py'): source_code,
        },
    }
    session.attempt_status = (
        AttemptSession.STATUS_COMPLETED if snapshot_type == SubmissionSnapshot.TYPE_SUBMIT else AttemptSession.STATUS_ACTIVE
    )
    session.save(update_fields=['answer_state', 'current_workspace_state', 'attempt_status', 'updated_at'])

    return snapshot, evaluation_run, legacy_submission


def evaluate_attempt_session(
    session: AttemptSession,
    *,
    snapshot_type: str,
    source_code: str = '',
    selected_options: list[str] | None = None,
    response_text: str = '',
    files: dict | None = None,
) -> tuple[SubmissionSnapshot, EvaluationRun, AIReview | None, Submission | None]:
    exercise = session.exercise
    if exercise is None:
        raise ValueError('Sessão sem exercício associado.')

    family_spec = get_family_spec(exercise.family_key)
    if snapshot_type not in family_spec.supported_snapshot_types:
        raise ValueError(f'Tipo de snapshot "{snapshot_type}" não suportado para {exercise.family_key}.')

    if exercise.family_key == ExerciseDefinition.FAMILY_CODE_LAB:
        snapshot, evaluation_run, legacy_submission = build_code_lab_evaluation(
            session=session,
            source_code=source_code,
            snapshot_type=snapshot_type,
        )
        review = AIReview.objects.filter(evaluation_run=evaluation_run).first()
        return snapshot, evaluation_run, review, legacy_submission

    if exercise.family_key == ExerciseDefinition.FAMILY_OBJECTIVE_ITEM:
        evaluation_plan = build_default_evaluation_plan(exercise)
        content_blocks = build_default_content_blocks(exercise)
        objective_result = evaluate_objective_selection(
            evaluation_plan=evaluation_plan,
            content_blocks=content_blocks,
            selected_options=selected_options,
            response_text=response_text,
            attempt_mode=session.mode,
        )
        snapshot = SubmissionSnapshot.objects.create(
            session=session,
            type=snapshot_type,
            payload={
                'selected_options': objective_result['selected_options'],
                'selected_labels': objective_result['selected_labels'],
                'response_text': response_text,
                'template': objective_result['template'],
                'choice_mode': objective_result['choice_mode'],
                'score_rule': objective_result['score_rule'],
            },
            files=files or {},
            selected_options=objective_result['selected_options'],
        )
        explanation_lines = [
            '### Revisão objetiva',
            f"Template avaliado: {objective_result['template']}",
            f"Você selecionou: {', '.join(objective_result['selected_labels']) if objective_result['selected_labels'] else '(nenhuma opção)'}",
            f"Gabarito esperado: {', '.join(objective_result['correct_labels']) if objective_result['correct_labels'] else '(sem gabarito definido)'}",
            '',
        ]
        if objective_result['template'] == 'compile-runtime-output':
            explanation_lines.append('A análise foi feita separando compilação, runtime e saída observável.')
            if objective_result['requires_output_text']:
                explanation_lines.append(f"Saída esperada: {objective_result['expected_output_text'] or '(sem saída configurada)'}")
                explanation_lines.append(f"Saída informada: {objective_result['response_text'] or '(nenhuma saída informada)'}")
                if objective_result['output_text_matches'] is False:
                    explanation_lines.append('A classificação apontou para output, mas o texto de saída ainda não bate com o esperado.')
        elif objective_result['template'] == 'behavior-classification':
            explanation_lines.append('O veredito depende do comportamento real do trecho, não apenas da leitura superficial do snippet.')
        elif objective_result['template'] == 'output-prediction':
            explanation_lines.append('A resposta foi avaliada como previsão de saída, com foco na execução linha a linha.')
        if objective_result['passed']:
            explanation_lines.append('Você acertou a leitura conceitual principal dessa questão.')
        else:
            explanation_lines.append('A resposta ainda não bate com o gabarito esperado.')
            if objective_result['correct_labels']:
                explanation_lines.append(
                    'Conceitos a revisar: ' + ', '.join(objective_result['correct_labels'])
                )
            wrong_explanations = [
                option.get('explanation')
                for option in objective_result['option_results']
                if option.get('selected') and not option.get('correct') and option.get('explanation')
            ]
            if wrong_explanations:
                explanation_lines.append('Explicações dos distratores escolhidos: ' + ' | '.join(dict.fromkeys(wrong_explanations)))
            if objective_result['misconception_inference']:
                explanation_lines.append(
                    'Conceitos a revisar: ' + ', '.join(objective_result['misconception_inference'])
                )
        correct_explanations = [
            option.get('explanation')
            for option in objective_result['option_results']
            if option.get('correct') and option.get('explanation')
        ]
        if correct_explanations:
            explanation_lines.append('Explicação da alternativa correta: ' + ' | '.join(dict.fromkeys(correct_explanations)))
        explanation_lines.extend(
            [
                '',
                'Pense na regra que diferencia a alternativa correta das distratoras e revise o enunciado com foco no ponto de decisão central.',
            ]
        )
        next_steps = [
            'Releia o enunciado e destaque a regra que decide a resposta correta.',
            'Compare as alternativas escolhidas com o gabarito e identifique a diferença conceitual principal.',
        ]
        if objective_result['misconception_inference']:
            next_steps.append(f"Revise os conceitos: {', '.join(objective_result['misconception_inference'])}.")

        evaluation_run = EvaluationRun.objects.create(
            submission=snapshot,
            evaluator_results={
                'family_key': exercise.family_key,
                'mechanism': objective_result['template'],
                'choice_mode': objective_result['choice_mode'],
                'selected_options': objective_result['selected_options'],
                'selected_labels': objective_result['selected_labels'],
                'correct_options': objective_result['correct_options'],
                'correct_labels': objective_result['correct_labels'],
                'passed': objective_result['passed'],
                'exact_match': objective_result['exact_match'],
                'score': objective_result['normalized_score'],
                'passing_score': objective_result['passing_score'],
                'option_results': objective_result['option_results'],
                'requires_output_text': objective_result['requires_output_text'],
                'expected_output_text': objective_result['expected_output_text'],
                'output_text_matches': objective_result['output_text_matches'],
                'response_text': objective_result['response_text'],
            },
            normalized_score=objective_result['normalized_score'],
            verdict=objective_result['verdict'],
            evidence_bundle={
                'statement': exercise.statement,
                'content_blocks': content_blocks,
                'workspace_spec': build_default_workspace_spec(exercise),
                'evaluation_plan': evaluation_plan,
                'template_meta': build_default_workspace_spec(exercise).get('template_meta', {}),
                'selected_options': objective_result['selected_options'],
                'selected_labels': objective_result['selected_labels'],
                'correct_options': objective_result['correct_options'],
                'correct_labels': objective_result['correct_labels'],
                'score_rule': objective_result['score_rule'],
                'option_results': objective_result['option_results'],
                'requires_output_text': objective_result['requires_output_text'],
                'expected_output_text': objective_result['expected_output_text'],
                'output_text_matches': objective_result['output_text_matches'],
                'response_text': objective_result['response_text'],
            },
            misconception_inference=objective_result['misconception_inference'],
            raw_artifacts={
                'response_text': response_text,
                'payload_selected_options': list(selected_options or []),
                'payload_files': files or {},
                'template': objective_result['template'],
                'choice_mode': objective_result['choice_mode'],
                'score_rule': objective_result['score_rule'],
            },
        )
        review = AIReview.objects.create(
            evaluation_run=evaluation_run,
            profile_key=exercise.review_profile,
            explanation='\n'.join(explanation_lines).strip(),
            next_steps=next_steps,
            conversation_thread=[
                {
                    'role': 'assistant',
                    'content': '\n'.join(explanation_lines).strip(),
                }
            ],
        )

        session.answer_state = {
            'selected_options': objective_result['selected_options'],
            'selected_labels': objective_result['selected_labels'],
            'response_text': response_text,
            'normalized_score': objective_result['normalized_score'],
            'verdict': objective_result['verdict'],
        }
        session.current_workspace_state = {
            **(session.current_workspace_state or {}),
            'selected_options': objective_result['selected_options'],
            'selected_labels': objective_result['selected_labels'],
            'response_text': response_text,
        }
        session.attempt_status = (
            AttemptSession.STATUS_COMPLETED if snapshot_type == SubmissionSnapshot.TYPE_SUBMIT else AttemptSession.STATUS_ACTIVE
        )
        session.save(update_fields=['answer_state', 'current_workspace_state', 'attempt_status', 'updated_at'])
        update_objective_item_progress(session.user, exercise, objective_result)
        return snapshot, evaluation_run, review, None

    snapshot = SubmissionSnapshot.objects.create(
        session=session,
        type=snapshot_type,
        payload={
            'source_code': source_code,
            'response_text': response_text,
        },
        files=files or {},
        selected_options=selected_options or [],
    )
    evaluation_run = EvaluationRun.objects.create(
        submission=snapshot,
        evaluator_results={
            'family_key': exercise.family_key,
            'mechanism': build_default_evaluation_plan(exercise).get('mechanism'),
        },
        normalized_score=0,
        verdict=EvaluationRun.VERDICT_ERROR,
        evidence_bundle={},
        misconception_inference=[],
        raw_artifacts={'status': 'not_implemented'},
    )
    review = AIReview.objects.create(
        evaluation_run=evaluation_run,
        profile_key=exercise.review_profile,
        explanation='Esta família ainda está em implementação na plataforma.',
        next_steps=['Volte a este exercício quando a família estiver habilitada.'],
        conversation_thread=[],
    )
    return snapshot, evaluation_run, review, None


def update_objective_item_progress(
    user: ArenaUser,
    exercise: ExerciseDefinition,
    objective_result: dict,
) -> tuple[UserExerciseProgress, list, int]:
    with transaction.atomic():
        locked_user = ArenaUser.objects.select_for_update().get(pk=user.pk)
        progress, _ = UserExerciseProgress.objects.select_for_update().get_or_create(
            user=locked_user,
            exercise=exercise,
        )

        progress.attempts_count += 1
        current_ratio = float(objective_result.get('normalized_score', 0) or 0)
        best_ratio = progress.best_ratio or 0
        improved = (
            current_ratio > best_ratio
            or (current_ratio == best_ratio and objective_result.get('passed') and progress.best_total_tests == 0)
        )

        if improved:
            progress.best_passed_tests = 1 if objective_result.get('passed') else 0
            progress.best_total_tests = 1
            progress.best_ratio = current_ratio

        awarded_progress_markers = list(progress.awarded_progress_markers or [])
        unlocked_rewards = []
        xp_awarded = 0

        if objective_result.get('passed') and 'passed_once' not in awarded_progress_markers:
            awarded_progress_markers.append('passed_once')
            unlocked_rewards.append(
                {
                    'milestone_key': 'passed_once',
                    'label': 'Primeira aprovação',
                    'xp_awarded': DEFAULT_OBJECTIVE_ITEM_XP,
                }
            )
            xp_awarded += DEFAULT_OBJECTIVE_ITEM_XP
            progress.first_passed_at = progress.first_passed_at or timezone.now()

        progress.awarded_progress_markers = awarded_progress_markers
        progress.xp_awarded_total += xp_awarded
        progress.save()

        if xp_awarded:
            locked_user.xp_total += xp_awarded
            locked_user.save(update_fields=['xp_total', 'updated_at'])

        user.xp_total = locked_user.xp_total
        return progress, unlocked_rewards, xp_awarded


def evaluate_submission(user: ArenaUser, exercise: ExerciseDefinition, source_code: str) -> tuple[Submission, list[dict]]:
    session = create_attempt_session_for_exercise(user, exercise, mode=AttemptSession.MODE_PRACTICE)
    _, evaluation_run, _, legacy_submission = evaluate_attempt_session(
        session,
        snapshot_type=SubmissionSnapshot.TYPE_SUBMIT,
        source_code=source_code,
    )
    if legacy_submission is None:
        raise ValueError('Submissão legada não foi criada para code_lab.')
    return legacy_submission, list(evaluation_run.evidence_bundle.get('results') or [])
