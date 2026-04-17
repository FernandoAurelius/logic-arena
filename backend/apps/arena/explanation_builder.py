from __future__ import annotations

from dataclasses import dataclass

from .models import Exercise, ExerciseTrack


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


@dataclass(frozen=True)
class ObjectiveOptionSeed:
    key: str
    marker: str
    text: str
    explanation: str
    is_correct: bool


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


def _get_exercise_type_label(exercise: Exercise) -> str:
    exercise_type = getattr(exercise, 'exercise_type', None)
    if exercise_type:
        return exercise_type.name
    return 'Drill de implementação'


def _format_objective_marker(raw: str, index: int) -> str:
    cleaned = raw.strip()
    if len(cleaned) == 1 and cleaned.isalpha():
        return cleaned.upper()
    return chr(65 + (index % 26))


def _extract_objective_options(exercise: Exercise) -> list[ObjectiveOptionSeed]:
    workspace_spec = exercise.workspace_spec or {}
    evaluation_plan = exercise.evaluation_plan or {}
    correct_options = {
        str(option).strip().lower()
        for option in evaluation_plan.get('correct_options', [])
        if str(option).strip()
    }

    raw_options = workspace_spec.get('options', [])
    if not isinstance(raw_options, list):
        return []

    options: list[ObjectiveOptionSeed] = []
    for index, raw_option in enumerate(raw_options):
        if not isinstance(raw_option, dict):
            continue
        key = str(raw_option.get('canonical_key') or raw_option.get('key') or '').strip()
        label = str(raw_option.get('label') or key or '').strip()
        marker = _format_objective_marker(label or key, index)
        text = _collapse_inline(
            str(
                raw_option.get('text')
                or raw_option.get('content')
                or raw_option.get('value')
                or raw_option.get('title')
                or label
                or key
                or 'Alternativa'
            )
        )
        explanation = _collapse_inline(str(raw_option.get('explanation') or ''))
        is_correct = (
            bool(raw_option.get('is_correct'))
            or bool(raw_option.get('correct'))
            or key.lower() in correct_options
            or label.lower() in correct_options
        )
        options.append(
            ObjectiveOptionSeed(
                key=key or label or marker.lower(),
                marker=marker,
                text=text,
                explanation=explanation,
                is_correct=is_correct,
            )
        )
    return options


def _build_objective_concepts(exercise: Exercise, track: ExerciseTrack | None) -> list[ExplanationConceptSeed]:
    track_concepts = getattr(track, 'concepts', None)
    concepts = [
        ExplanationConceptSeed(
            title=concept.title,
            explanation_text=concept.summary,
            why_it_matters=concept.why_it_matters,
            common_mistake=concept.common_mistake,
        )
        for concept in (track_concepts.all() if track_concepts is not None else ())
    ]
    if concepts:
        return concepts

    fallback_summary = _collapse_inline(exercise.concept_summary or exercise.pedagogical_brief or exercise.statement)
    fallback_why = _collapse_inline(exercise.professor_note or exercise.pedagogical_brief or exercise.concept_summary)
    fallback_mistake = (
        str(exercise.misconception_tags[0]).replace('_', ' ')
        if exercise.misconception_tags
        else 'Responder por impressão geral sem verificar o conceito realmente cobrado.'
    )
    return [
        ExplanationConceptSeed(
            title=exercise.title,
            explanation_text=fallback_summary,
            why_it_matters=fallback_why,
            common_mistake=fallback_mistake,
        )
    ]


def _build_objective_blueprint(exercise: Exercise, track: ExerciseTrack | None) -> ExplanationBlueprint:
    exercise_type_label = _get_exercise_type_label(exercise)
    statement_excerpt = _first_non_empty_line(exercise.statement) or exercise.title
    pedagogical_brief = _collapse_inline(exercise.pedagogical_brief)
    professor_note = _collapse_inline(exercise.professor_note)
    options = _extract_objective_options(exercise)
    correct_options = [option for option in options if option.is_correct]
    distractors = [option for option in options if not option.is_correct]
    concepts = _build_objective_concepts(exercise, track)
    concept_titles = ', '.join(concept.title for concept in concepts[:3]) if concepts else 'leitura conceitual'
    track_goal = _collapse_inline(getattr(track, 'goal', '') or getattr(track, 'description', '') or '')
    main_correct = correct_options[0] if correct_options else None

    focus_copy = pedagogical_brief or exercise.concept_summary or statement_excerpt
    question_focus = (
        f'Esta questão mede principalmente **{concept_titles}**. '
        f'O núcleo da decisão está em reconhecer o que o enunciado pede sem confundir com categorias vizinhas.'
    )
    if track_goal:
        question_focus += f' No contexto da trilha, isso reforça: {track_goal}.'

    identification_steps = [
        '1. Leia o enunciado procurando a palavra ou relação que realmente decide a resposta.',
        '2. Isole o conceito central antes de olhar para as alternativas.',
        '3. Compare cada alternativa com o que o enunciado afirma literalmente.',
        '4. Elimine primeiro as opções que trocam categoria, época, papel ou definição.',
    ]
    if main_correct is not None and main_correct.explanation:
        identification_steps.append(
            f'5. A alternativa **{main_correct.marker}** sobrevive porque {main_correct.explanation}.'
        )

    distractor_lines = []
    for option in distractors[:4]:
        rationale = option.explanation or 'ela parece plausível, mas não corresponde ao conceito pedido.'
        distractor_lines.append(f'- **{option.marker}. {option.text}**: {rationale}')
    if not distractor_lines:
        distractor_lines.append('- Elimine toda alternativa que responda a outra pergunta diferente da que foi feita.')

    common_mistakes = [
        *(concept.common_mistake for concept in concepts if concept.common_mistake),
        *(tag.replace('_', ' ') for tag in (exercise.misconception_tags or [])),
    ]
    deduped_common_mistakes = list(dict.fromkeys(item for item in common_mistakes if item))[:5]
    if not deduped_common_mistakes:
        deduped_common_mistakes = [
            'Responder pela impressão geral sem voltar ao enunciado.',
            'Confundir o conceito principal com uma categoria parecida.',
        ]

    mastery_checklist = [
        'Consigo dizer em uma frase qual conceito a questão está cobrando.',
        'Sei justificar por que a alternativa correta responde exatamente ao enunciado.',
        'Consigo explicar por que pelo menos um distrator parece plausível, mas está errado.',
        'Consigo refazer a decisão sem depender de chute ou de eliminação superficial.',
    ]

    assessment_notes = (
        f'Em **{exercise_type_label}**, a cobrança aqui é de leitura conceitual e discriminação entre alternativas próximas. '
        f'O enunciado-base é: **{statement_excerpt}**.'
    )
    if professor_note:
        assessment_notes += f'\n\nObservação do professor: {professor_note}.'

    implementation_strategy = (
        'Use a decisão em duas camadas:\n'
        '- primeiro, confirme qual conceito ou relação o enunciado está cobrando;\n'
        '- depois, compare esse filtro com cada alternativa sem adicionar interpretação extra.\n\n'
        '**Como eliminar os distratores**\n'
        + '\n'.join(distractor_lines)
    )
    if main_correct is not None:
        main_rationale = main_correct.explanation or 'é a única que responde ao conceito pedido sem trocar a categoria em jogo.'
        implementation_strategy += (
            f'\n\n**Alternativa correta e por quê**\n'
            f'- **{main_correct.marker}. {main_correct.text}**: {main_rationale}'
        )

    return ExplanationBlueprint(
        learning_goal=(
            f'Consolidar a leitura conceitual por trás de `{exercise.title}`, reconhecendo o foco real da questão '
            f'e justificando a alternativa correta com critérios de {exercise_type_label}.'
        ),
        concept_focus_markdown=(
            question_focus
            + (
                f'\n\nResumo útil do módulo: {focus_copy}.'
                if focus_copy
                else ''
            )
        ),
        reading_strategy_markdown='\n'.join(identification_steps),
        implementation_strategy_markdown=implementation_strategy,
        assessment_notes_markdown=assessment_notes,
        common_mistakes=deduped_common_mistakes,
        mastery_checklist=mastery_checklist,
        concepts=concepts,
        code_examples=[],
    )


def _build_code_examples(exercise: Exercise, track: ExerciseTrack | None) -> list[ExplanationCodeExampleSeed]:
    topic = _normalize_topic(
        ' '.join(
            filter(
                None,
                    [
                        exercise.title,
                        exercise.statement,
                        exercise.professor_note,
                        getattr(track, 'description', '') if track else '',
                        getattr(track, 'goal', '') if track else '',
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
    track = getattr(exercise, 'track', None)
    if getattr(exercise, 'family_key', None) == Exercise.FAMILY_OBJECTIVE_ITEM:
        return _build_objective_blueprint(exercise, track)

    exercise_type_label = _get_exercise_type_label(exercise)
    statement_excerpt = _first_non_empty_line(exercise.statement) or exercise.title
    professor_note = _collapse_inline(exercise.professor_note)
    sample_input = _collapse_inline(exercise.sample_input)
    sample_output = _collapse_inline(exercise.sample_output)
    track_concepts = getattr(track, 'concepts', None)
    track_prerequisites = getattr(track, 'prerequisites', None)
    concepts = [
        ExplanationConceptSeed(
            title=concept.title,
            explanation_text=concept.summary,
            why_it_matters=concept.why_it_matters,
            common_mistake=concept.common_mistake,
        )
        for concept in (track_concepts.all() if track_concepts is not None else ())
    ]
    concept_titles = ', '.join(concept.title for concept in concepts) if concepts else 'leitura precisa do enunciado'
    prerequisites = (
        [prerequisite.label for prerequisite in track_prerequisites.all()]
        if track_prerequisites is not None
        else ['Leitura atenta do enunciado', 'Saída exata com `print`']
    )
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
        code_examples=_build_code_examples(exercise, track),
    )
