import re
import secrets
import json
import threading
from typing import Any
from dataclasses import asdict, dataclass
from urllib.error import URLError
from urllib.request import Request, urlopen

from django.contrib.auth.hashers import check_password, make_password
from django.conf import settings
from django.db import close_old_connections, transaction
from django.utils import timezone

from .explanation_builder import build_explanation_blueprint
from .models import (
    ArenaUser,
    AuthSession,
    Exercise,
    ExerciseCategory,
    ExerciseExplanation,
    ExerciseExplanationCodeExample,
    ExerciseExplanationConcept,
    ExerciseTestCase,
    ExerciseTrackConcept,
    ExerciseTrackPrerequisite,
    ExerciseTrack,
    ExerciseType,
    LearningModule,
    Submission,
    UserExerciseProgress,
)
from .http_contracts import evaluate_http_contract
from .feedback import build_feedback_error_payload, generate_feedback


NUMERIC_TOLERANCE = 1e-9
PASSED_ONCE_MARKER = 'passed_once'
PASSED_ONCE_XP = 35
DEFAULT_EXERCISE_TYPE_SLUG = 'drill-de-implementacao'
DEFAULT_EXERCISE_TYPE_LABEL = 'Drill de implementação'
FAMILY_CODE_LAB = 'code_lab'
FAMILY_CONTRACT_HTTP = 'contract_behavior_lab'
SURFACE_CODE_SINGLE = 'code_editor_single'
SURFACE_CODE_MULTIFILE = 'code_editor_multifile'
SURFACE_HTTP_CONTRACT = 'http_contract_lab'

APPROVAL_PATTERNS = {
    'approved': [
        'aluno aprovado',
        'aprovado',
        'aluno passou',
        'passou',
    ],
    'failed': [
        'aluno reprovado',
        'reprovado',
        'aluno reprovou',
        'reprovou',
    ],
}


def normalize_text(text: str) -> str:
    return str(text).replace('\r', '').strip()


def canonical_text(text: str) -> str:
    return re.sub(r'\s+', ' ', normalize_text(text).lower())


def detect_status_intent(text: str) -> str | None:
    canonical = canonical_text(text)
    for status, patterns in APPROVAL_PATTERNS.items():
        if any(pattern in canonical for pattern in patterns):
            return status
    return None


def extract_numeric_tokens(text: str) -> list[float]:
    return [float(token) for token in re.findall(r'-?\d+(?:\.\d+)?', normalize_text(text))]


def line_matches(expected_line: str, actual_output: str) -> bool:
    try:
        expected_number = float(expected_line)
        return any(abs(number - expected_number) < NUMERIC_TOLERANCE for number in extract_numeric_tokens(actual_output))
    except ValueError:
        expected_status = detect_status_intent(expected_line)
        actual_status = detect_status_intent(actual_output)
        if expected_status is not None and actual_status is not None:
            return expected_status == actual_status
        return canonical_text(expected_line) in canonical_text(actual_output)


def outputs_match(expected: str, actual: str) -> bool:
    expected_normalized = normalize_text(expected)
    actual_normalized = normalize_text(actual)

    if expected_normalized == actual_normalized:
        return True

    return all(line_matches(expected_line, actual_normalized) for expected_line in expected_normalized.split('\n'))


def deep_merge_dicts(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = deep_merge_dicts(merged[key], value)
        else:
            merged[key] = value
    return merged


def resolve_exercise_family_key(exercise: Exercise) -> str:
    workspace_family = (exercise.workspace_spec or {}).get('family_key')
    if isinstance(workspace_family, str) and workspace_family.strip():
        return workspace_family.strip()
    if isinstance(exercise.family_key, str) and exercise.family_key.strip():
        return exercise.family_key.strip()
    return FAMILY_CODE_LAB


def build_default_workspace_spec(exercise: Exercise) -> dict[str, Any]:
    family_key = resolve_exercise_family_key(exercise)
    if family_key == FAMILY_CONTRACT_HTTP:
        return {
            'family_key': FAMILY_CONTRACT_HTTP,
            'surface_key': SURFACE_HTTP_CONTRACT,
            'workspace_kind': 'http_contract',
            'contract': {
                'request': {
                    'method': 'GET',
                    'path': '/health',
                    'headers': {},
                    'body': None,
                    'examples': [],
                },
                'response': {
                    'status_code': 200,
                    'headers': {'content-type': 'application/json'},
                    'body': {'ok': True},
                    'body_schema': {
                        'type': 'object',
                        'required': ['ok'],
                        'properties': {
                            'ok': {'type': 'boolean'},
                        },
                    },
                },
            },
        }

    return {
        'family_key': FAMILY_CODE_LAB,
        'surface_key': SURFACE_CODE_SINGLE,
        'workspace_kind': 'single_file',
        'language': exercise.language or 'python',
        'entrypoint': 'main.py',
        'files': [
            {
                'path': 'main.py',
                'content': exercise.starter_code or '# Escreva sua solução aqui\n',
                'readonly': False,
            },
        ],
    }


def build_default_evaluation_plan(exercise: Exercise) -> dict[str, Any]:
    workspace_spec = build_default_workspace_spec(exercise)
    if resolve_exercise_family_key(exercise) == FAMILY_CONTRACT_HTTP:
        contract = workspace_spec.get('contract', {})
        return {
            'family_key': FAMILY_CONTRACT_HTTP,
            'checks': ['status', 'headers', 'body', 'body_schema'],
            'weights': {
                'status': 0.35,
                'headers': 0.2,
                'body': 0.25,
                'body_schema': 0.2,
            },
            'contract': contract,
        }

    return {
        'family_key': FAMILY_CODE_LAB,
        'checks': ['tests'],
        'weights': {'tests': 1.0},
    }


def resolve_workspace_spec(exercise: Exercise) -> dict[str, Any]:
    default_spec = build_default_workspace_spec(exercise)
    persisted_spec = exercise.workspace_spec or {}
    if not persisted_spec:
        return default_spec
    return deep_merge_dicts(default_spec, persisted_spec)


def resolve_evaluation_plan(exercise: Exercise) -> dict[str, Any]:
    default_plan = build_default_evaluation_plan(exercise)
    persisted_plan = exercise.evaluation_plan or {}
    if not persisted_plan:
        return default_plan
    return deep_merge_dicts(default_plan, persisted_plan)


def get_or_create_session(nickname: str, password: str) -> tuple[AuthSession, bool]:
    user = ArenaUser.objects.filter(nickname=nickname).first()
    created = False

    if user is None:
        user = ArenaUser.objects.create(nickname=nickname, password_hash=make_password(password))
        created = True
    elif not check_password(password, user.password_hash):
        raise ValueError('Nickname já existe, mas a senha não confere.')

    session = AuthSession.objects.create(user=user, token=secrets.token_hex(32))
    return session, created


def create_exercise(payload) -> Exercise:
    category = None
    track = None
    module = None
    exercise_type = None
    if payload.category_slug and payload.category_name:
        category, _ = ExerciseCategory.objects.get_or_create(
            slug=payload.category_slug,
            defaults={'name': payload.category_name},
        )
    if payload.module_slug and payload.module_name:
        module, _ = LearningModule.objects.get_or_create(
            slug=payload.module_slug,
            defaults={
                'name': payload.module_name,
                'description': payload.module_description,
                'audience': payload.module_audience,
                'source_kind': payload.module_source_kind,
                'status': LearningModule.STATUS_ACTIVE,
            },
        )
    if payload.track_slug and payload.track_name and category is not None:
        track, _ = ExerciseTrack.objects.get_or_create(
            slug=payload.track_slug,
            defaults={
                'name': payload.track_name,
                'category': category,
                'module': module,
            },
        )
    elif payload.track_slug:
        track = ExerciseTrack.objects.filter(slug=payload.track_slug).first()

    if payload.exercise_type_slug:
        exercise_type = ExerciseType.objects.filter(slug=payload.exercise_type_slug).first()
    if exercise_type is None:
        exercise_type = ExerciseType.objects.filter(slug=DEFAULT_EXERCISE_TYPE_SLUG).first()

    exercise_stub = Exercise(
        slug=payload.slug,
        title=payload.title,
        statement=payload.statement,
        family_key=(payload.family_key or FAMILY_CODE_LAB).strip() if getattr(payload, 'family_key', '') else FAMILY_CODE_LAB,
        difficulty=payload.difficulty,
        language=payload.language,
    )
    workspace_spec = deep_merge_dicts(build_default_workspace_spec(exercise_stub), getattr(payload, 'workspace_spec', {}) or {})
    evaluation_plan = deep_merge_dicts(build_default_evaluation_plan(exercise_stub), getattr(payload, 'evaluation_plan', {}) or {})

    exercise = Exercise.objects.create(
        slug=payload.slug,
        title=payload.title,
        statement=payload.statement,
        family_key=exercise_stub.family_key,
        difficulty=payload.difficulty,
        language=payload.language,
        category=category or (track.category if track else None),
        track=track,
        exercise_type=exercise_type,
        content_blocks=list(getattr(payload, 'content_blocks', []) or []),
        workspace_spec=workspace_spec,
        evaluation_plan=evaluation_plan,
        review_profile=dict(getattr(payload, 'review_profile', {}) or {}),
        estimated_time_minutes=payload.estimated_time_minutes,
        track_position=payload.track_position,
        concept_summary=payload.concept_summary,
        pedagogical_brief=payload.pedagogical_brief,
        starter_code=payload.starter_code,
        sample_input=payload.sample_input,
        sample_output=payload.sample_output,
        professor_note=payload.professor_note,
    )
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
    sync_exercise_explanation(exercise)
    return exercise


@dataclass
class ExecutionResult:
    ok: bool
    stdout: str
    stderr: str


@dataclass
class ProgressReward:
    milestone_key: str
    label: str
    xp_awarded: int


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


def compute_level_from_xp(xp_total: int) -> int:
    return max(1, (xp_total // 100) + 1)


def build_user_progress_summary(user: ArenaUser) -> dict:
    xp_total = user.xp_total
    level = compute_level_from_xp(xp_total)
    xp_into_level = xp_total - ((level - 1) * 100)
    return {
        'xp_total': xp_total,
        'level': level,
        'xp_into_level': xp_into_level,
        'xp_to_next_level': max(0, 100 - xp_into_level),
    }


def build_user_schema_payload(user: ArenaUser) -> dict:
    return {
        'id': user.id,
        'nickname': user.nickname,
        'created_at': user.created_at,
        **build_user_progress_summary(user),
    }


def build_exercise_progress_payload(progress: UserExerciseProgress) -> dict:
    return {
        'attempts_count': progress.attempts_count,
        'best_passed_tests': progress.best_passed_tests,
        'best_total_tests': progress.best_total_tests,
        'best_ratio': progress.best_ratio,
        'xp_awarded_total': progress.xp_awarded_total,
        'first_passed_at': progress.first_passed_at,
        'awarded_progress_markers': progress.awarded_progress_markers,
    }


def build_exercise_catalog_meta(exercise: Exercise) -> dict:
    exercise_type = exercise.exercise_type.slug if exercise.exercise_type else DEFAULT_EXERCISE_TYPE_SLUG
    workspace_spec = resolve_workspace_spec(exercise)
    return {
        'exercise_type': exercise_type,
        'exercise_type_label': exercise.exercise_type.name if exercise.exercise_type else DEFAULT_EXERCISE_TYPE_LABEL,
        'family_key': resolve_exercise_family_key(exercise),
        'surface_key': workspace_spec.get('surface_key', SURFACE_CODE_SINGLE),
        'workspace_kind': workspace_spec.get('workspace_kind', 'single_file'),
        'estimated_time_minutes': exercise.estimated_time_minutes or 15,
        'concept_summary': exercise.concept_summary or exercise.professor_note,
        'pedagogical_brief': exercise.pedagogical_brief or exercise.professor_note,
        'track_position': exercise.track_position or 0,
    }


def build_track_progress_index(user: ArenaUser, exercises: list[Exercise]) -> dict[int, UserExerciseProgress]:
    progress_entries = UserExerciseProgress.objects.filter(
        user=user,
        exercise__in=exercises,
    ).select_related('exercise')
    return {entry.exercise_id: entry for entry in progress_entries}


def build_track_progress_summary(track: ExerciseTrack, user: ArenaUser) -> dict:
    exercises = list(track.exercises.filter(is_active=True).select_related('category', 'track', 'exercise_type', 'track__module'))
    exercises.sort(key=lambda exercise: ((exercise.track_position or 9999), exercise.title))
    progress_index = build_track_progress_index(user, exercises)
    completed = 0
    current_target = None

    for exercise in exercises:
        progress = progress_index.get(exercise.id)
        passed_once = bool(progress and PASSED_ONCE_MARKER in (progress.awarded_progress_markers or []))
        if passed_once:
            completed += 1
            continue
        if current_target is None:
            current_target = exercise

    progress_percent = round((completed / len(exercises)) * 100) if exercises else 0

    return {
        'track': track,
        'exercises': exercises,
        'progress_index': progress_index,
        'completed': completed,
        'total': len(exercises),
        'progress_percent': progress_percent,
        'current_target': current_target,
    }


def build_module_progress_summary(module: LearningModule, user: ArenaUser) -> dict:
    tracks = list(module.tracks.select_related('category', 'module').all())
    track_summaries = [build_track_progress_summary(track, user) for track in tracks]
    completed_tracks = sum(1 for summary in track_summaries if summary['total'] > 0 and summary['completed'] == summary['total'])
    current_target_track = next((summary['track'] for summary in track_summaries if summary['current_target'] is not None), None)
    current_target_exercise = next((summary['current_target'] for summary in track_summaries if summary['current_target'] is not None), None)
    progress_percent = round((completed_tracks / len(tracks)) * 100) if tracks else 0
    return {
        'module': module,
        'tracks': track_summaries,
        'completed_tracks': completed_tracks,
        'total_tracks': len(tracks),
        'progress_percent': progress_percent,
        'current_target_track': current_target_track,
        'current_target_exercise': current_target_exercise,
    }


def sync_exercise_explanation(exercise: Exercise) -> ExerciseExplanation:
    blueprint = build_explanation_blueprint(exercise)
    explanation, _ = ExerciseExplanation.objects.update_or_create(
        exercise=exercise,
        defaults={
            'learning_goal': blueprint.learning_goal,
            'concept_focus_markdown': blueprint.concept_focus_markdown,
            'reading_strategy_markdown': blueprint.reading_strategy_markdown,
            'implementation_strategy_markdown': blueprint.implementation_strategy_markdown,
            'assessment_notes_markdown': blueprint.assessment_notes_markdown,
            'common_mistakes': blueprint.common_mistakes,
            'mastery_checklist': blueprint.mastery_checklist,
        },
    )

    explanation.concepts.all().delete()
    explanation.code_examples.all().delete()

    ExerciseExplanationConcept.objects.bulk_create(
        [
            ExerciseExplanationConcept(
                explanation=explanation,
                title=concept.title,
                explanation_text=concept.explanation_text,
                why_it_matters=concept.why_it_matters,
                common_mistake=concept.common_mistake,
                sort_order=index,
            )
            for index, concept in enumerate(blueprint.concepts, start=1)
        ]
    )

    ExerciseExplanationCodeExample.objects.bulk_create(
        [
            ExerciseExplanationCodeExample(
                explanation=explanation,
                title=example.title,
                rationale=example.rationale,
                language=example.language,
                code=example.code,
                sort_order=index,
            )
            for index, example in enumerate(blueprint.code_examples, start=1)
        ]
    )

    return explanation


def ensure_exercise_explanation(exercise: Exercise) -> ExerciseExplanation:
    explanation = ExerciseExplanation.objects.filter(exercise=exercise).first()
    if explanation is not None:
        return explanation
    return sync_exercise_explanation(exercise)


def apply_submission_progress(user: ArenaUser, exercise: Exercise, submission: Submission) -> tuple[UserExerciseProgress, list[ProgressReward], int]:
    with transaction.atomic():
        locked_user = ArenaUser.objects.select_for_update().get(pk=user.pk)
        progress, _ = UserExerciseProgress.objects.select_for_update().get_or_create(
            user=locked_user,
            exercise=exercise,
        )

        progress.attempts_count += 1
        progress.last_submission = submission

        total_tests = submission.total_tests
        current_ratio = (submission.passed_tests / total_tests) if total_tests else 0
        best_ratio = progress.best_ratio or 0
        improved = (
            current_ratio > best_ratio
            or submission.passed_tests > progress.best_passed_tests
            or (submission.passed_tests == progress.best_passed_tests and total_tests > progress.best_total_tests)
        )

        if improved:
            progress.best_passed_tests = submission.passed_tests
            progress.best_total_tests = total_tests
            progress.best_ratio = current_ratio
            progress.best_progress_submission = submission

        awarded_progress_markers = list(progress.awarded_progress_markers or [])
        unlocked_rewards: list[ProgressReward] = []
        xp_awarded = 0

        if submission.status == Submission.STATUS_PASSED and PASSED_ONCE_MARKER not in awarded_progress_markers:
            awarded_progress_markers.append(PASSED_ONCE_MARKER)
            unlocked_rewards.append(
                ProgressReward(
                    milestone_key=PASSED_ONCE_MARKER,
                    label='Primeira aprovação',
                    xp_awarded=PASSED_ONCE_XP,
                )
            )
            xp_awarded += PASSED_ONCE_XP
            progress.first_passed_at = progress.first_passed_at or timezone.now()
            progress.first_pass_submission = progress.first_pass_submission or submission

        progress.awarded_progress_markers = awarded_progress_markers
        progress.xp_awarded_total += xp_awarded
        progress.save()

        if xp_awarded:
            locked_user.xp_total += xp_awarded
            locked_user.save(update_fields=['xp_total', 'updated_at'])

        submission.xp_awarded = xp_awarded
        submission.unlocked_progress_rewards = [asdict(reward) for reward in unlocked_rewards]
        submission.save(update_fields=['xp_awarded', 'unlocked_progress_rewards', 'updated_at'])

        user.xp_total = locked_user.xp_total
        return progress, unlocked_rewards, xp_awarded


def _payload_to_dict(payload: Any) -> dict[str, Any]:
    if hasattr(payload, 'model_dump'):
        return dict(payload.model_dump())
    if isinstance(payload, dict):
        return dict(payload)
    raise TypeError('Payload de submissão deve ser um dict ou schema compatível.')


def build_submission_review_context(exercise: Exercise, submission: Submission, results: list[dict[str, Any]]) -> dict[str, Any]:
    workspace_spec = resolve_workspace_spec(exercise)
    evaluation_plan = resolve_evaluation_plan(exercise)
    return {
        'family_key': resolve_exercise_family_key(exercise),
        'surface_key': workspace_spec.get('surface_key'),
        'workspace_spec': workspace_spec,
        'evaluation_plan': evaluation_plan,
        'submission_payload': submission.submission_payload,
        'evidence_bundle': submission.evidence_bundle,
        'results': results,
        'console_output': submission.console_output,
        'source_code': submission.source_code,
        'exercise_title': exercise.title,
        'exercise_statement': exercise.statement,
    }


def _build_code_lab_results(exercise: Exercise, source_code: str) -> tuple[list[dict[str, Any]], str, int, int]:
    results: list[dict[str, Any]] = []

    for index, test_case in enumerate(exercise.test_cases.all(), start=1):
        execution = run_python(source_code, test_case.input_data)
        actual_output = normalize_text(execution.stdout)
        expected_output = normalize_text(test_case.expected_output)
        passed = execution.ok and outputs_match(expected_output, actual_output)
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
    console_output = '\n\n'.join(
        [
            '\n'.join(
                [
                    f"Teste {result['index']}: {'PASSOU' if result['passed'] else 'FALHOU'}",
                    f"Entrada: {result['input_data']!r}",
                    f"Esperado: {result['expected_output']}",
                    f"Obtido: {result['actual_output'] or '(sem saída)'}",
                    *([f"Erro: {result['stderr']}"] if result['stderr'] else []),
                ]
            )
            for result in results
        ]
    )
    return results, console_output, passed_tests, total_tests


def _build_code_lab_evidence(exercise: Exercise, results: list[dict[str, Any]], passed_tests: int, total_tests: int) -> dict[str, Any]:
    workspace_spec = resolve_workspace_spec(exercise)
    return {
        'family_key': resolve_exercise_family_key(exercise),
        'surface_key': workspace_spec.get('surface_key'),
        'workspace_kind': workspace_spec.get('workspace_kind'),
        'test_results': results,
        'passed_checks': passed_tests,
        'total_checks': total_tests,
    }


def _build_contract_submission_evidence(exercise: Exercise, payload: dict[str, Any], evaluation: Any) -> dict[str, Any]:
    workspace_spec = resolve_workspace_spec(exercise)
    evaluation_plan = resolve_evaluation_plan(exercise)
    expected_request = (evaluation_plan.get('contract') or {}).get('request') or workspace_spec.get('contract', {}).get('request') or {}
    expected_response = (evaluation_plan.get('contract') or {}).get('response') or workspace_spec.get('contract', {}).get('response') or {}
    return {
        'family_key': resolve_exercise_family_key(exercise),
        'surface_key': workspace_spec.get('surface_key'),
        'workspace_kind': workspace_spec.get('workspace_kind'),
        'request': expected_request,
        'expected_response': expected_response,
        'observed_response': {
            'status': payload.get('response_status'),
            'headers': payload.get('response_headers', {}),
            'body': payload.get('response_body', ''),
        },
        'checks': evaluation.results,
        'divergences': evaluation.evidence_bundle.get('divergences', []),
        'passed_checks': evaluation.passed_tests,
        'total_checks': evaluation.total_tests,
    }


def evaluate_submission(user: ArenaUser, exercise: Exercise, payload: Any) -> tuple[Submission, list[dict]]:
    submission_payload = _payload_to_dict(payload)
    family_key = resolve_exercise_family_key(exercise)

    if family_key == FAMILY_CONTRACT_HTTP:
        workspace_spec = resolve_workspace_spec(exercise)
        evaluation_plan = resolve_evaluation_plan(exercise)
        contract_spec = evaluation_plan.get('contract') or workspace_spec.get('contract') or {}
        evaluation = evaluate_http_contract(
            family_key=family_key,
            surface_key=workspace_spec.get('surface_key', SURFACE_HTTP_CONTRACT),
            request_spec=contract_spec.get('request') or {},
            response_spec=contract_spec.get('response') or {},
            submission_payload=submission_payload,
        )
        source_code = str(submission_payload.get('source_code', '') or '')
        status = Submission.STATUS_PASSED if evaluation.status == 'passed' else Submission.STATUS_FAILED
        submission = Submission.objects.create(
            user=user,
            exercise=exercise,
            source_code=source_code,
            submission_payload=submission_payload,
            evidence_bundle=evaluation.evidence_bundle,
            status=status,
            passed_tests=evaluation.passed_tests,
            total_tests=evaluation.total_tests,
            console_output=evaluation.console_output,
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
            execution_results=evaluation.results,
            review_chat_history=[],
            xp_awarded=0,
            unlocked_progress_rewards=[],
        )
        apply_submission_progress(user, exercise, submission)
        _start_feedback_job(
            submission.id,
            exercise.title,
            exercise.statement,
            source_code,
            evaluation.passed_tests,
            evaluation.total_tests,
            evaluation.results,
            build_submission_review_context(exercise, submission, evaluation.results),
        )
        return submission, evaluation.results

    source_code = str(submission_payload.get('source_code', '') or '')
    results, console_output, passed_tests, total_tests = _build_code_lab_results(exercise, source_code)
    passed = total_tests > 0 and passed_tests == total_tests
    status = Submission.STATUS_PASSED if passed else Submission.STATUS_FAILED
    submission = Submission.objects.create(
        user=user,
        exercise=exercise,
        source_code=source_code,
        submission_payload=submission_payload,
        evidence_bundle=_build_code_lab_evidence(exercise, results, passed_tests, total_tests),
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
    _start_feedback_job(
        submission.id,
        exercise.title,
        exercise.statement,
        source_code,
        passed_tests,
        total_tests,
        results,
        build_submission_review_context(exercise, submission, results),
    )
    return submission, results


def _start_feedback_job(
    submission_id: int,
    exercise_title: str,
    statement: str,
    source_code: str,
    passed_tests: int,
    total_tests: int,
    results: list[dict],
    context: dict[str, Any] | None = None,
) -> None:
    def job() -> None:
        close_old_connections()
        try:
            feedback_payload = generate_feedback(
                exercise_title=exercise_title,
                statement=statement,
                source_code=source_code,
                passed_tests=passed_tests,
                total_tests=total_tests,
                results=results,
                context=context,
            )
            Submission.objects.filter(id=submission_id).update(
                feedback=feedback_payload.summary,
                feedback_status=Submission.FEEDBACK_READY,
                feedback_source=feedback_payload.source,
                feedback_payload=feedback_payload.model_dump(),
                review_chat_history=[
                    {
                        'role': 'assistant',
                        'content': '\n'.join(
                            [
                                f"### Revisão automática",
                                feedback_payload.summary,
                                '',
                                '**Pontos fortes**',
                                *[f"- {item}" for item in feedback_payload.strengths],
                                '',
                                '**Ajustes**',
                                *[f"- {item}" for item in feedback_payload.issues],
                                '',
                                '**Próximos passos**',
                                *[f"- {item}" for item in feedback_payload.next_steps],
                            ]
                        ).strip(),
                    }
                ],
            )
        except Exception as error:
            payload = build_feedback_error_payload(error)
            Submission.objects.filter(id=submission_id).update(
                feedback=payload.summary,
                feedback_status=Submission.FEEDBACK_ERROR,
                feedback_source=payload.source,
                feedback_payload=payload.model_dump(),
                review_chat_history=[
                    {
                        'role': 'assistant',
                        'content': payload.summary,
                    }
                ],
            )
        finally:
            close_old_connections()

    threading.Thread(target=job, daemon=True).start()
