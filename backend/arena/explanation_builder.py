from __future__ import annotations

from dataclasses import dataclass

from .catalog import EXERCISE_TYPE_LABELS, TRACK_CATALOG, TrackMeta
from .models import Exercise


@dataclass(frozen=True)
class ExplanationConceptSeed:
    title: str
    explanation_text: str
    why_it_matters: str
    common_mistake: str


@dataclass(frozen=True)
class ExplanationCodeExampleSeed:
    title: str
    rationale: str
    language: str
    code: str


@dataclass(frozen=True)
class ExplanationBlueprint:
    learning_goal: str
    concept_focus_markdown: str
    reading_strategy_markdown: str
    implementation_strategy_markdown: str
    assessment_notes_markdown: str
    common_mistakes: list[str]
    mastery_checklist: list[str]
    concepts: list[ExplanationConceptSeed]
    code_examples: list[ExplanationCodeExampleSeed]


def _normalize_topic(value: str) -> str:
    return (
        value.lower()
        .replace('á', 'a')
        .replace('à', 'a')
        .replace('ã', 'a')
        .replace('â', 'a')
        .replace('é', 'e')
        .replace('ê', 'e')
        .replace('í', 'i')
        .replace('ó', 'o')
        .replace('ô', 'o')
        .replace('õ', 'o')
        .replace('ú', 'u')
        .replace('ç', 'c')
    )


def _has_any_keyword(topic: str, keywords: list[str]) -> bool:
    return any(keyword in topic for keyword in keywords)


def _first_non_empty_line(value: str) -> str:
    for line in value.splitlines():
        cleaned = line.strip()
        if cleaned:
            return cleaned
    return ''


def _collapse_inline(value: str) -> str:
    return ' '.join(part.strip() for part in value.splitlines() if part.strip())


def _get_track_meta(exercise: Exercise) -> TrackMeta | None:
    if not exercise.track:
        return None
    return TRACK_CATALOG.get(exercise.track.slug)


def _get_exercise_type_label(exercise: Exercise) -> str:
    track_meta = _get_track_meta(exercise)
    if not track_meta:
        return 'Core Drill'
    exercise_meta = track_meta.exercise_meta.get(exercise.slug)
    if not exercise_meta:
        return 'Core Drill'
    return EXERCISE_TYPE_LABELS.get(exercise_meta.exercise_type, 'Core Drill')


def _build_code_examples(exercise: Exercise, track_meta: TrackMeta | None) -> list[ExplanationCodeExampleSeed]:
    topic = _normalize_topic(
        ' '.join(
            filter(
                None,
                [
                    exercise.title,
                    exercise.statement,
                    exercise.professor_note,
                    track_meta.description if track_meta else '',
                    track_meta.goal if track_meta else '',
                ],
            )
        )
    )

    examples: list[ExplanationCodeExampleSeed] = []

    if _has_any_keyword(topic, ['media', 'aprovacao', 'nota']):
        examples.append(
            ExplanationCodeExampleSeed(
                title='Leitura de entradas com decisão condicional',
                rationale='Exemplo clássico de cálculo seguido por classificação com `if/else`.',
                language='python',
                code="""nota1 = float(input())
nota2 = float(input())
media = (nota1 + nota2) / 2

if media >= 5:
    print("Aluno aprovado.")
else:
    print("Aluno reprovado.")""",
            )
        )

    if _has_any_keyword(topic, ['range', 'impar', 'par', 'naturais', 'sequencia', 'intervalo', 'for']):
        examples.append(
            ExplanationCodeExampleSeed(
                title='Controle de sequência com `range`',
                rationale='Mostra como transformar um intervalo em repetição determinística sem errar limites.',
                language='python',
                code="""limite = int(input())

for numero in range(1, limite + 1):
    if numero % 2 != 0:
        print(numero)""",
            )
        )

    if _has_any_keyword(topic, ['maior', 'menor', 'comparacao', 'prioridade', 'valor']):
        examples.append(
            ExplanationCodeExampleSeed(
                title='Comparação com atualização de referência',
                rationale='Útil para módulos em que o conceito central é decidir qual valor tem prioridade.',
                language='python',
                code="""a = int(input())
b = int(input())

if a > b:
    print(a)
else:
    print(b)""",
            )
        )

    if _has_any_keyword(topic, ['soma', 'contador', 'acumulador']):
        examples.append(
            ExplanationCodeExampleSeed(
                title='Acumulador simples com repetição',
                rationale='Serve de base para problemas que pedem totalização progressiva.',
                language='python',
                code="""quantidade = int(input())
soma = 0

for _ in range(quantidade):
    valor = int(input())
    soma += valor

print(soma)""",
            )
        )

    if _has_any_keyword(topic, ['fahrenheit', 'celsius', 'triangulo', 'formula', 'area']):
        examples.append(
            ExplanationCodeExampleSeed(
                title='Aplicação direta de fórmula',
                rationale='Mostra o padrão objetivo de entrada, cálculo e saída para módulos baseados em fórmula.',
                language='python',
                code="""valor = float(input())
convertido = (valor - 32) * 5 / 9
print(convertido)""",
            )
        )

    examples.append(
        ExplanationCodeExampleSeed(
            title='Esqueleto técnico mínimo do módulo',
            rationale='Template universal para reconhecer a sequência correta de leitura, regra principal e saída.',
            language='python',
            code="""# 1. Ler entradas
entrada = input().strip()

# 2. Converter se necessário
valor = int(entrada)

# 3. Aplicar a regra principal
resultado = valor

# 4. Exibir apenas a saída exigida
print(resultado)""",
        )
    )

    deduped: list[ExplanationCodeExampleSeed] = []
    seen_titles: set[str] = set()
    for example in examples:
        if example.title in seen_titles:
            continue
        deduped.append(example)
        seen_titles.add(example.title)
    return deduped[:3]


def build_explanation_blueprint(exercise: Exercise) -> ExplanationBlueprint:
    track_meta = _get_track_meta(exercise)
    exercise_type_label = _get_exercise_type_label(exercise)
    statement_excerpt = _first_non_empty_line(exercise.statement) or exercise.title
    professor_note = _collapse_inline(exercise.professor_note)
    sample_input = _collapse_inline(exercise.sample_input)
    sample_output = _collapse_inline(exercise.sample_output)
    concepts = [
        ExplanationConceptSeed(
            title=concept.title,
            explanation_text=concept.summary,
            why_it_matters=concept.why_it_matters,
            common_mistake=concept.common_mistake,
        )
        for concept in (track_meta.concepts if track_meta else ())
    ]
    concept_titles = ', '.join(concept.title for concept in concepts) if concepts else 'leitura precisa do enunciado'
    prerequisites = list(track_meta.prerequisites) if track_meta else ['Leitura atenta do enunciado', 'Saída exata com `print`']
    contextual_note = f' Observação do professor: {professor_note}.' if professor_note else ''
    io_contract = ''
    if sample_input or sample_output:
        io_contract = (
            '\n\n### Contrato operacional de I/O\n'
            f'- **Entrada de referência:** `{sample_input or "não informado"}`\n'
            f'- **Saída de referência:** `{sample_output or "não informada"}`\n'
            '- Use esse contrato para validar ordem de leitura, conversão de tipo e formatação final antes de submeter.'
        )

    return ExplanationBlueprint(
        learning_goal=(
            f'Consolidar o padrão técnico por trás de `{exercise.title}`, transformando o conceito principal '
            f'em uma estrutura de código curta, correta e compatível com cobrança de {exercise_type_label}.'
        ),
        concept_focus_markdown=(
            f'Este módulo gira em torno de **{concept_titles}**. '
            f'O enunciado-base é: **{statement_excerpt}**. '
            'A leitura correta aqui não é só "entender o que fazer", mas identificar qual estrutura mental do problema está sendo cobrada '
            'e transformá-la em código sem adicionar ruído desnecessário.'
            f'{contextual_note}'
            f'{io_contract}'
        ),
        reading_strategy_markdown=(
            'Leia o enunciado procurando quatro decisões obrigatórias:\n'
            '1. **Quais entradas existem** e em qual ordem elas chegam.\n'
            '2. **Como cada entrada deve ser convertida** (`int`, `float`, texto puro, contador, acumulador).\n'
            '3. **Qual é a regra central do problema**, isto é, a decisão ou transformação que realmente gera o resultado.\n'
            '4. **Qual é o formato exato da saída**, porque muitos erros de prova acontecem com lógica certa e impressão errada.\n\n'
            f'No contexto deste módulo, a primeira frase útil do enunciado é: **{statement_excerpt}**. '
            'Se qualquer uma dessas quatro partes ficar nebulosa, a implementação tende a nascer errada.'
        ),
        implementation_strategy_markdown=(
            f'Em termos de implementação, trate `{exercise.title}` como um módulo de estrutura simples e progressiva:\n'
            '1. Modele primeiro a leitura das entradas.\n'
            '2. Faça as conversões de tipo imediatamente após a leitura.\n'
            '3. Isole a regra principal em uma variável ou bloco pequeno.\n'
            '4. Só então escreva a saída final, sem mensagens extras.\n\n'
            'A solução correta quase sempre nasce de uma cadeia curta de decisões, e não de uma estrutura complexa. '
            'Se o código começar a crescer demais, isso costuma ser sinal de que a regra central ainda não foi isolada direito.'
        ),
        assessment_notes_markdown=(
            f'Em **{exercise_type_label}**, a banca normalmente valoriza clareza, obediência ao enunciado '
            'e aderência total ao formato de saída. O erro comum não é “não saber programar”, mas errar a leitura, '
            'a ordem da decisão ou o tipo de variável usado no cálculo.\n\n'
            f'Neste módulo, revise especialmente: **{statement_excerpt}**. '
            'Antes de considerar a solução pronta, compare a sua saída com o contrato de I/O e confirme que você não adicionou texto explicativo desnecessário.'
        ),
        common_mistakes=[
            'Começar a codar antes de identificar a regra principal do exercício.',
            'Acertar a lógica mas errar o formato de saída esperado.',
            'Usar a estrutura de controle errada para o padrão cobrado.',
            *[concept.common_mistake for concept in concepts if concept.common_mistake],
        ],
        mastery_checklist=[
            'Consigo explicar em uma frase qual é a regra principal do módulo.',
            'Sei quais variáveis precisam existir antes de começar a codar.',
            'Sei qual estrutura usar: fórmula, condição, laço, acumulador ou combinação delas.',
            'Consigo escrever uma solução curta sem sacrificar precisão.',
            *prerequisites,
        ],
        concepts=concepts,
        code_examples=_build_code_examples(exercise, track_meta),
    )
