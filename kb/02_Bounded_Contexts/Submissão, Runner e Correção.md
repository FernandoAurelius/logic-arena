# Submissão, Runner e Correção

## Objetivo do módulo

Este é o coração operacional da plataforma. É aqui que o código do aluno vira execução real, comparação com expectativa e resultado persistido.

## Arquivos principais

- `backend/arena/services.py`
- `backend/arena/api.py`
- `runner_service/app.py`
- `backend/arena/models.py`

## Fluxo atual

1. o frontend envia `source_code` para `POST /api/submissions/exercises/{slug}/submit`;
2. o backend carrega o exercício e seus casos de teste;
3. para cada caso, chama o runner por HTTP;
4. normaliza saída esperada e obtida;
5. calcula `passed_tests`, `total_tests` e `status`;
6. persiste a submissão;
7. devolve o resultado imediatamente ao frontend.

## Trecho de código central

```python
for index, test_case in enumerate(exercise.test_cases.all(), start=1):
    execution = run_python(source_code, test_case.input_data)
    actual_output = normalize_text(execution.stdout)
    expected_output = normalize_text(test_case.expected_output)
    passed = execution.ok and outputs_match(expected_output, actual_output)
```

Esse trecho mostra um ponto importante: a correção não depende apenas de igualdade textual crua. Existe uma camada de tolerância semântica para não reprovar soluções corretas por pequenas diferenças aceitáveis.

## Comparação semântica

Uma decisão prática foi flexibilizar certas comparações:

- tolerância numérica para ponto flutuante;
- reconhecimento de intenções equivalentes como `aprovado/passou` e `reprovado/reprovou`;
- aceitação de saídas textualmente maiores quando elas ainda contêm a resposta relevante.

Isso melhora a experiência para treino, mas também introduz uma tensão: correção pedagógica mais amigável nem sempre é igual à rigidez de um judge de prova.

## Por que o runner separado importa

O backend principal não executa Python arbitrário diretamente. Em vez disso:

```python
request = Request(
    f'{settings.RUNNER_URL}/execute/python',
    data=payload,
    headers={'Content-Type': 'application/json'},
    method='POST',
)
```

Esse desenho separa:

- domínio do produto;
- execução potencialmente perigosa;
- observabilidade e hardening futuro.

## Tensões abertas

- o modelo ainda não diferencia modos de correção mais rígidos vs mais tolerantes;
- falta persistir melhor metadados de avaliação para ranking e mastery;
- ainda não há suporte a múltiplas linguagens.

## Por onde continuar

- [[Revisão com IA]]
- [[../04_Milestones/M1 - Integridade da Progressão]]
