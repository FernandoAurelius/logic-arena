import json
from dataclasses import dataclass
from urllib.error import URLError
from urllib.request import Request, urlopen

from django.conf import settings

from apps.arena.models import ArenaUser, Exercise, Submission, UserExerciseProgress
from apps.practice.domain import format_execution_results_console, normalize_text, outputs_match_robust
from apps.progress.application.services import apply_submission_progress, build_exercise_progress_payload, build_user_progress_summary
from apps.review.application.services import schedule_submission_feedback


DEFAULT_EXERCISE_TYPE_SLUG = 'drill-de-implementacao'
DEFAULT_EXERCISE_TYPE_LABEL = 'Drill de implementação'


def build_exercise_catalog_meta(exercise: Exercise) -> dict:
    exercise_type = exercise.exercise_type.slug if exercise.exercise_type else DEFAULT_EXERCISE_TYPE_SLUG
    return {
        'exercise_type': exercise_type,
        'exercise_type_label': exercise.exercise_type.name if exercise.exercise_type else DEFAULT_EXERCISE_TYPE_LABEL,
        'estimated_time_minutes': exercise.estimated_time_minutes or 15,
        'concept_summary': exercise.concept_summary or exercise.professor_note,
        'pedagogical_brief': exercise.pedagogical_brief or exercise.professor_note,
        'track_position': exercise.track_position or 0,
    }


def serialize_exercise_summary(exercise: Exercise) -> dict:
    meta = build_exercise_catalog_meta(exercise)
    return {
        'id': exercise.id,
        'slug': exercise.slug,
        'title': exercise.title,
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


def serialize_exercise_detail(exercise: Exercise) -> dict:
    return {
        **serialize_exercise_summary(exercise),
        'statement': exercise.statement,
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
        'exercise_progress': build_exercise_progress_payload(progress) if progress else {
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


def evaluate_submission(user: ArenaUser, exercise: Exercise, source_code: str) -> tuple[Submission, list[dict]]:
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
    passed = total_tests > 0 and passed_tests == total_tests
    status = Submission.STATUS_PASSED if passed else Submission.STATUS_FAILED
    console_output = format_execution_results_console(results)

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
    schedule_submission_feedback(submission.id, exercise.title, exercise.statement, source_code, passed_tests, total_tests, results)
    return submission, results
