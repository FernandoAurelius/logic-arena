import re
import secrets
import json
import threading
from dataclasses import dataclass
from urllib.error import URLError
from urllib.request import Request, urlopen

from django.contrib.auth.hashers import check_password, make_password
from django.conf import settings
from django.db import close_old_connections

from .models import ArenaUser, AuthSession, Exercise, ExerciseTestCase, Submission
from .feedback import build_feedback_error_payload, generate_feedback


NUMERIC_TOLERANCE = 1e-9

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
    exercise = Exercise.objects.create(
        slug=payload.slug,
        title=payload.title,
        statement=payload.statement,
        difficulty=payload.difficulty,
        language=payload.language,
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
    return exercise


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
    passed = total_tests > 0 and passed_tests == total_tests
    status = Submission.STATUS_PASSED if passed else Submission.STATUS_FAILED
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
    )
    _start_feedback_job(submission.id, exercise.title, exercise.statement, source_code, passed_tests, total_tests, results)
    return submission, results


def _start_feedback_job(
    submission_id: int,
    exercise_title: str,
    statement: str,
    source_code: str,
    passed_tests: int,
    total_tests: int,
    results: list[dict],
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
