import re

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


def outputs_match_robust(expected: str, actual: str) -> bool:
    expected_normalized = normalize_text(expected)
    actual_normalized = normalize_text(actual)

    if expected_normalized == actual_normalized:
        return True

    return all(line_matches(expected_line, actual_normalized) for expected_line in expected_normalized.split('\n'))


def format_execution_results_console(results: list[dict]) -> str:
    return '\n\n'.join(
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

