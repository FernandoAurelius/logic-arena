from apps.practice.domain import (
    canonical_text,
    detect_status_intent,
    extract_numeric_tokens,
    format_execution_results_console,
    line_matches,
    outputs_match_robust,
)


def test_practice_domain_matches_numeric_status_and_canonical_text():
    assert outputs_match_robust('3.5', '3.5000000001')
    assert line_matches('aprovado', 'Aluno passou com sucesso')
    assert detect_status_intent('Aluno reprovado') == 'failed'
    assert canonical_text('  Olá   mundo  ') == 'olá mundo'
    assert extract_numeric_tokens('x=1 e y=-2.5') == [1.0, -2.5]


def test_practice_domain_formats_console_output():
    console = format_execution_results_console(
        [
            {
                'index': 1,
                'input_data': '1\n',
                'expected_output': '1',
                'actual_output': '1',
                'passed': True,
                'stderr': '',
            },
            {
                'index': 2,
                'input_data': '2\n',
                'expected_output': '2',
                'actual_output': '3',
                'passed': False,
                'stderr': 'boom',
            },
        ]
    )

    assert 'Teste 1: PASSOU' in console
    assert 'Teste 2: FALHOU' in console
    assert 'Erro: boom' in console

