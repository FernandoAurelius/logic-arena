from dataclasses import dataclass


@dataclass(frozen=True)
class TrackConcept:
    title: str
    summary: str
    why_it_matters: str
    common_mistake: str


@dataclass(frozen=True)
class ExerciseMeta:
    exercise_type: str
    estimated_time_minutes: int
    concept_summary: str
    pedagogical_brief: str


@dataclass(frozen=True)
class TrackMeta:
    level_label: str
    goal: str
    description: str
    concept_kicker: str
    concepts: tuple[TrackConcept, ...]
    prerequisites: tuple[str, ...]
    milestone_title: str
    milestone_summary: str
    milestone_requirement_label: str
    exercise_order: tuple[str, ...]
    exercise_meta: dict[str, ExerciseMeta]

TRACK_CATALOG: dict[str, TrackMeta] = {
    # Na M2, a taxonomia canônica da navegação continua curada em código.
    # exercise_type, estimated_time_minutes e exercise_order ficam aqui de forma deliberada
    # até a milestone em que o catálogo precisar ser editável sem deploy.
    'entrada-saida-e-formulas': TrackMeta(
        level_label='Base Operacional',
        goal='Dominar leitura, conversão e fórmulas diretas sem ruído.',
        description='Esta trilha consolida a base da prova prática: ler entradas corretamente, converter tipos e aplicar fórmulas sem desviar do formato esperado.',
        concept_kicker='Conceitos nucleares',
        concepts=(
            TrackConcept(
                title='Leitura e conversão',
                summary='Receber dados e converter para o tipo certo antes de calcular.',
                why_it_matters='Quase toda questão da prova começa com leitura precisa de entrada.',
                common_mistake='Esquecer `float` ou `int` e operar strings sem perceber.',
            ),
            TrackConcept(
                title='Fórmula direta',
                summary='Aplicar uma expressão matemática sem criar etapas desnecessárias.',
                why_it_matters='Questões iniciais valorizam precisão e objetividade.',
                common_mistake='Trocar a ordem da fórmula ou usar divisão inteira sem querer.',
            ),
        ),
        prerequisites=('Leitura de enunciado', 'Saída simples com `print`'),
        milestone_title='Checkpoint de Precisão',
        milestone_summary='Uma mini simulação que mistura leitura, tipo numérico e formatação direta.',
        milestone_requirement_label='Complete todos os drills-base da trilha.',
        exercise_order=(
            'soma-simples',
            'area-triangulo',
            'fahrenheit-celsius',
        ),
        exercise_meta={
            'soma-simples': ExerciseMeta(
                exercise_type='core_drill',
                estimated_time_minutes=10,
                concept_summary='Leitura inteira e soma direta.',
                pedagogical_brief='Exercício de aquecimento para validar entrada, conversão e saída limpa.',
            ),
            'area-triangulo': ExerciseMeta(
                exercise_type='exam_simulation',
                estimated_time_minutes=15,
                concept_summary='Float, fórmula e atenção ao resultado esperado.',
                pedagogical_brief='Questão clássica de prova: pouca ajuda, cálculo direto e tolerância baixa a distrações.',
            ),
            'fahrenheit-celsius': ExerciseMeta(
                exercise_type='core_drill',
                estimated_time_minutes=12,
                concept_summary='Aplicação de fórmula com parênteses e conversão.',
                pedagogical_brief='Treina precisão algébrica antes de avançar para condicionais.',
            ),
        },
    ),
    'condicionais-basicas': TrackMeta(
        level_label='Decisão Fundamental',
        goal='Ler cenários simples e classificar corretamente com if/elif/else.',
        description='Esta trilha introduz tomada de decisão com foco em cenários comuns de prova: comparação, classificação, menu simples e mensagens condicionais.',
        concept_kicker='Padrões de decisão',
        concepts=(
            TrackConcept(
                title='Classificação condicional',
                summary='Escolher um único caminho a partir de critérios simples.',
                why_it_matters='Boa parte das questões intermediárias começa com um if puro.',
                common_mistake='Usar vários `if` quando o caso exige exclusividade entre cenários.',
            ),
            TrackConcept(
                title='Comparação e prioridade',
                summary='Comparar valores e respeitar a ordem correta dos testes.',
                why_it_matters='A ordem das condições altera totalmente o comportamento da solução.',
                common_mistake='Testar casos mais genéricos antes dos específicos.',
            ),
        ),
        prerequisites=('Entrada numérica básica', 'Fórmulas simples'),
        milestone_title='Gatekeeper Condicional',
        milestone_summary='Simulação curta cobrando múltiplos ramos sem ajuda visual.',
        milestone_requirement_label='Passe nos módulos centrais da trilha.',
        exercise_order=(),
        exercise_meta={},
    ),
    'flags-e-while': TrackMeta(
        level_label='Controle de Fluxo',
        goal='Controlar repetição por sentinela, flag e acumuladores simples.',
        description='Aqui a trilha troca resolução pontual por processamento contínuo de entradas, exigindo atenção ao laço, ao término e ao estado acumulado.',
        concept_kicker='Controle contínuo',
        concepts=(
            TrackConcept(
                title='While com sentinela',
                summary='Continuar lendo até um valor de parada.',
                why_it_matters='É um padrão recorrente de prova e ensina controle explícito de fluxo.',
                common_mistake='Processar o valor sentinela como se fosse dado válido.',
            ),
            TrackConcept(
                title='Acumuladores e contadores',
                summary='Guardar totais, quantidades e extremos durante a repetição.',
                why_it_matters='Quase toda questão com loop exige algum estado intermediário.',
                common_mistake='Inicializar mal o acumulador ou esquecer de atualizá-lo dentro do laço.',
            ),
        ),
        prerequisites=('If/else básico', 'Operadores relacionais'),
        milestone_title='Milestone de Fluxo',
        milestone_summary='Checkpoint que mistura parada por sentinela com múltiplos acumuladores.',
        milestone_requirement_label='Concluir os exercícios de leitura contínua e contagem.',
        exercise_order=(),
        exercise_meta={},
    ),
    'sequencias-e-for': TrackMeta(
        level_label='Sequências e Iteração',
        goal='Percorrer intervalos com clareza e dominar padrões clássicos de `for`.',
        description='Esta trilha trabalha sequências determinísticas, progressões, limites e médias controladas por repetição conhecida.',
        concept_kicker='Iteração determinística',
        concepts=(
            TrackConcept(
                title='Range e limites',
                summary='Definir início, fim e passo corretamente.',
                why_it_matters='Questões com `for` costumam falhar por off-by-one ou passo errado.',
                common_mistake='Esquecer que o limite superior do `range` não é incluído.',
            ),
            TrackConcept(
                title='Sequência orientada por entrada',
                summary='Adaptar o laço ao intervalo informado pelo usuário.',
                why_it_matters='É a ponte entre `for` básico e problemas mais flexíveis.',
                common_mistake='Não tratar direção crescente/decrescente corretamente.',
            ),
        ),
        prerequisites=('While e comparação simples', 'Impressão linha a linha'),
        milestone_title='Simulação de Sequências',
        milestone_summary='Checkpoint focado em progressões, médias e direção de intervalo.',
        milestone_requirement_label='Dominar os drills de `for` antes do simulado.',
        exercise_order=(),
        exercise_meta={},
    ),
}


EXERCISE_TYPE_LABELS = {
    'core_drill': 'Exercício-base',
    'exam_simulation': 'Simulação de prova',
    'guided_build': 'Construção guiada',
    'integrative_case': 'Caso integrador',
}
