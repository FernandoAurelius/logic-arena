import os
import re
import secrets
import json
from dataclasses import dataclass
from urllib.error import URLError
from urllib.request import Request, urlopen

from django.contrib.auth.hashers import check_password, make_password
from django.conf import settings

from .models import ArenaUser, AuthSession, Exercise, ExerciseTestCase, Submission


NUMERIC_TOLERANCE = 1e-9


def normalize_text(text: str) -> str:
    return str(text).replace('\r', '').strip()


def canonical_text(text: str) -> str:
    return re.sub(r'\s+', ' ', normalize_text(text).lower())


def extract_numeric_tokens(text: str) -> list[float]:
    return [float(token) for token in re.findall(r'-?\d+(?:\.\d+)?', normalize_text(text))]


def line_matches(expected_line: str, actual_output: str) -> bool:
    try:
        expected_number = float(expected_line)
        return any(abs(number - expected_number) < NUMERIC_TOLERANCE for number in extract_numeric_tokens(actual_output))
    except ValueError:
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


def build_submission_feedback(exercise: Exercise, passed: bool, passed_tests: int, total_tests: int) -> str:
    if passed:
        return (
            f'Você passou em todos os testes de "{exercise.title}". '
            'Na próxima iteração, vale revisar legibilidade, nomes e aderência ao estilo da prova.'
        )

    return (
        f'Você passou em {passed_tests} de {total_tests} testes em "{exercise.title}". '
        'Releia o enunciado, compare sua saída com o esperado e cheque entrada, formatação e casos-limite.'
    )


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
        feedback=build_submission_feedback(exercise, passed, passed_tests, total_tests),
    )
    return submission, results
