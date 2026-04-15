import json
from dataclasses import dataclass
from urllib.error import URLError
from urllib.request import Request, urlopen

from django.conf import settings

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
from apps.practice.application.registry import get_family_spec, resolve_surface_key
from apps.practice.domain import format_execution_results_console, normalize_text, outputs_match_robust
from apps.progress.application.services import apply_submission_progress, build_exercise_progress_payload, build_user_progress_summary
from apps.review.application.services import schedule_submission_feedback


DEFAULT_EXERCISE_TYPE_SLUG = 'drill-de-implementacao'
DEFAULT_EXERCISE_TYPE_LABEL = 'Drill de implementação'


def build_default_content_blocks(exercise: ExerciseDefinition) -> list[dict]:
    if exercise.content_blocks:
        return list(exercise.content_blocks)
    return [
        {
            'kind': 'statement',
            'title': exercise.title,
            'content': exercise.statement,
        }
    ]


def build_default_workspace_spec(exercise: ExerciseDefinition) -> dict:
    if exercise.workspace_spec:
        return dict(exercise.workspace_spec)

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
    serialized_progress = None
    if latest_snapshot is not None:
        latest_evaluation = latest_snapshot.evaluation_runs.order_by('-created_at', '-id').first()
        if latest_evaluation is not None:
            latest_review = getattr(latest_evaluation, 'ai_review', None)
        if latest_snapshot.legacy_submission is not None:
            serialized_progress = serialize_submission(latest_snapshot.legacy_submission)

    exercise = session.exercise
    assessment = session.assessment
    family_key = exercise.family_key if exercise else None
    surface_key = None
    if exercise is not None:
        surface_key = resolve_surface_key(exercise)
    elif isinstance(session.state, dict):
        surface_key = session.state.get('surface_key')

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
    return AttemptSession.objects.create(
        user=user,
        target_type=AttemptSession.TARGET_EXERCISE,
        exercise=exercise,
        mode=mode,
        state={'family_key': exercise.family_key, 'surface_key': resolve_surface_key(exercise)},
        current_workspace_state=workspace_spec,
        answer_state={'source_code': exercise.starter_code} if exercise.family_key == ExerciseDefinition.FAMILY_CODE_LAB else {},
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
