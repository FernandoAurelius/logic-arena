from django.db import migrations


EXERCISE_TYPES = [
    {
        'slug': 'rastreamento-e-leitura',
        'name': 'Rastreamento e leitura',
        'description': 'Foco em interpretação do enunciado, leitura de entrada e previsão de comportamento.',
        'sort_order': 1,
    },
    {
        'slug': 'drill-de-implementacao',
        'name': 'Drill de implementação',
        'description': 'Implementação direta e objetiva de uma solução curta.',
        'sort_order': 2,
    },
    {
        'slug': 'correcao-de-codigo',
        'name': 'Correção de código',
        'description': 'Exercício voltado a diagnosticar e corrigir uma solução quebrada.',
        'sort_order': 3,
    },
    {
        'slug': 'implementacao-guiada',
        'name': 'Implementação guiada',
        'description': 'Resolução com algum apoio estrutural ou decomposição sugerida.',
        'sort_order': 4,
    },
    {
        'slug': 'checkpoint-de-trilha',
        'name': 'Checkpoint de trilha',
        'description': 'Exercício de consolidação ao fim de um bloco de conteúdo.',
        'sort_order': 5,
    },
    {
        'slug': 'caso-integrador',
        'name': 'Caso integrador',
        'description': 'Problema que combina múltiplos conceitos e etapas.',
        'sort_order': 6,
    },
    {
        'slug': 'exam-like',
        'name': 'Exam-like',
        'description': 'Formato mais rígido, inspirado em prova ou certificação.',
        'sort_order': 7,
    },
]


MODULES = [
    {
        'slug': 'logica-de-programacao-com-python',
        'name': 'Lógica de Programação com Python',
        'description': 'Percurso base de algoritmos, sintaxe Python e resolução progressiva de problemas inspirado no livro do Nilo Ney Coutinho Menezes.',
        'audience': 'Iniciantes em programação e alunos em preparação prática',
        'source_kind': 'livro-curado',
        'status': 'active',
        'sort_order': 1,
    },
    {
        'slug': 'desenvolvimento-web-com-fastapi',
        'name': 'Desenvolvimento Web com FastAPI',
        'description': 'Scaffold inicial para trilhas de backend HTTP, validação, serviços e persistência.',
        'audience': 'Alunos saindo da lógica e entrando em backend Python',
        'source_kind': 'scaffold',
        'status': 'draft',
        'sort_order': 2,
    },
    {
        'slug': 'desenvolvimento-frontend-com-vue',
        'name': 'Desenvolvimento Front-end com Vue',
        'description': 'Scaffold inicial para trilhas de componentes, estado e integração com APIs.',
        'audience': 'Alunos evoluindo para front-end moderno',
        'source_kind': 'scaffold',
        'status': 'draft',
        'sort_order': 3,
    },
    {
        'slug': 'integracao-full-stack',
        'name': 'Integração Full-stack',
        'description': 'Scaffold inicial para módulos que conectam frontend, backend e contratos HTTP.',
        'audience': 'Alunos em fase de integração entre camadas',
        'source_kind': 'scaffold',
        'status': 'draft',
        'sort_order': 4,
    },
    {
        'slug': 'preparatorio-ocp-17',
        'name': 'Preparatório OCP 17',
        'description': 'Scaffold inicial para trilhas exam-like voltadas à certificação Java OCP 17.',
        'audience': 'Estudantes em preparação para certificação',
        'source_kind': 'scaffold',
        'status': 'draft',
        'sort_order': 5,
    },
]


CATEGORIES = [
    {'slug': 'fundamentos-python', 'name': 'Fundamentos de Python', 'description': 'Base de sintaxe, entrada, saída e estruturas elementares.', 'sort_order': 10},
    {'slug': 'estruturas-e-algoritmos', 'name': 'Estruturas e Algoritmos', 'description': 'Condições, repetições, coleções e decomposição.', 'sort_order': 20},
    {'slug': 'persistencia-e-modelagem', 'name': 'Persistência e Modelagem', 'description': 'Arquivos, objetos e bancos de dados.', 'sort_order': 30},
    {'slug': 'web-backend', 'name': 'Web Backend', 'description': 'HTTP, APIs e serviços.', 'sort_order': 40},
    {'slug': 'frontend-moderno', 'name': 'Frontend Moderno', 'description': 'Componentes, estado e interface.', 'sort_order': 50},
    {'slug': 'integracao-de-sistemas', 'name': 'Integração de Sistemas', 'description': 'Contratos, integração e fluxo entre camadas.', 'sort_order': 60},
    {'slug': 'certificacoes', 'name': 'Certificações', 'description': 'Trilhas orientadas a exames e simulados.', 'sort_order': 70},
]


TRACKS = [
    {
        'slug': 'ambiente-e-primeiros-programas',
        'module_slug': 'logica-de-programacao-com-python',
        'category_slug': 'fundamentos-python',
        'name': 'Ambiente e primeiros programas',
        'description': 'Onboarding prático do ambiente, execução e mentalidade inicial de programação.',
        'goal': 'Ganhar segurança com execução, arquivo fonte e primeiros programas.',
        'level_label': 'Onboarding',
        'concept_kicker': 'Começo operacional',
        'milestone_title': 'Pronto para codar',
        'milestone_summary': 'Checkpoint leve para validar leitura do ambiente e fluxo básico de execução.',
        'milestone_requirement_label': 'Passe pelos exercícios iniciais do módulo.',
        'sort_order': 1,
        'concepts': [
            {'title': 'Fluxo básico de execução', 'summary': 'Entender o ciclo editar, executar, observar saída.', 'why_it_matters': 'Reduz atrito antes de entrar no conteúdo lógico.', 'common_mistake': 'Focar cedo demais em sintaxe avançada.', 'sort_order': 1},
            {'title': 'Leitura operacional do enunciado', 'summary': 'Começar a identificar entrada, processamento e saída.', 'why_it_matters': 'É a base para todos os exercícios seguintes.', 'common_mistake': 'Codar antes de saber o que entra e o que sai.', 'sort_order': 2},
        ],
        'prerequisites': [
            {'label': 'Conseguir rodar um programa Python simples', 'sort_order': 1},
        ],
    },
    {
        'slug': 'variaveis-tipos-e-entrada-de-dados',
        'module_slug': 'logica-de-programacao-com-python',
        'category_slug': 'fundamentos-python',
        'name': 'Variáveis, tipos e entrada de dados',
        'description': 'Entrada, conversão, armazenamento em variáveis e fórmulas diretas.',
        'goal': 'Dominar leitura, conversão e saída limpa em Python.',
        'level_label': 'Fundamentos',
        'concept_kicker': 'Base da linguagem',
        'milestone_title': 'Checkpoint de precisão numérica',
        'milestone_summary': 'Consolida leitura, tipo e fórmulas sem ruído.',
        'milestone_requirement_label': 'Complete os drills-base da trilha.',
        'sort_order': 2,
        'concepts': [
            {'title': 'Variáveis e atribuição', 'summary': 'Guardar valores de entrada e intermediários com clareza.', 'why_it_matters': 'Toda solução limpa depende de variáveis bem escolhidas.', 'common_mistake': 'Misturar leitura, cálculo e saída numa linha só cedo demais.', 'sort_order': 1},
            {'title': 'Conversão de entrada', 'summary': 'Transformar `input()` no tipo certo antes de operar.', 'why_it_matters': 'Evita bugs silenciosos com strings.', 'common_mistake': 'Esquecer `int` ou `float`.', 'sort_order': 2},
        ],
        'prerequisites': [
            {'label': 'Leitura atenta do enunciado', 'sort_order': 1},
            {'label': 'Saída simples com `print`', 'sort_order': 2},
        ],
    },
    {
        'slug': 'condicoes',
        'module_slug': 'logica-de-programacao-com-python',
        'category_slug': 'estruturas-e-algoritmos',
        'name': 'Condições',
        'description': 'Tomada de decisão com `if`, `elif` e `else` em cenários práticos.',
        'goal': 'Classificar cenários e decidir corretamente com estruturas condicionais.',
        'level_label': 'Decisão',
        'concept_kicker': 'Escolha de caminho',
        'milestone_title': 'Gate condicional',
        'milestone_summary': 'Simulação curta de múltiplos ramos e prioridade de testes.',
        'milestone_requirement_label': 'Passe pelos exercícios centrais da trilha.',
        'sort_order': 3,
        'concepts': [
            {'title': 'Comparação e prioridade', 'summary': 'Respeitar a ordem correta dos testes.', 'why_it_matters': 'A ordem das condições muda o comportamento do programa.', 'common_mistake': 'Testar o caso geral antes do específico.', 'sort_order': 1},
            {'title': 'Exclusividade entre cenários', 'summary': 'Usar `if/elif/else` quando só um caminho deve acontecer.', 'why_it_matters': 'Evita lógica duplicada e saídas incoerentes.', 'common_mistake': 'Usar vários `if` independentes.', 'sort_order': 2},
        ],
        'prerequisites': [
            {'label': 'Variáveis numéricas e lógicas', 'sort_order': 1},
            {'label': 'Operadores relacionais básicos', 'sort_order': 2},
        ],
    },
    {
        'slug': 'repeticoes',
        'module_slug': 'logica-de-programacao-com-python',
        'category_slug': 'estruturas-e-algoritmos',
        'name': 'Repetições',
        'description': 'Laços com `while` e `for`, sentinela, contadores e acumuladores.',
        'goal': 'Controlar repetição e estado incremental com segurança.',
        'level_label': 'Fluxo',
        'concept_kicker': 'Iteração e estado',
        'milestone_title': 'Checkpoint de repetição',
        'milestone_summary': 'Consolida laços, parada, contadores e acumuladores.',
        'milestone_requirement_label': 'Concluir os exercícios-base de repetição.',
        'sort_order': 4,
        'concepts': [
            {'title': 'Laço com sentinela', 'summary': 'Processar entradas até um valor de parada.', 'why_it_matters': 'É um padrão frequente em provas e exercícios de lógica.', 'common_mistake': 'Contar ou processar a sentinela como dado válido.', 'sort_order': 1},
            {'title': 'Acumuladores e contadores', 'summary': 'Guardar totais, quantidades e extremos ao longo do laço.', 'why_it_matters': 'Permite resolver médias, totais e rastreamento de melhor/pior valor.', 'common_mistake': 'Inicializar ou atualizar o acumulador errado.', 'sort_order': 2},
        ],
        'prerequisites': [
            {'label': 'Condições simples com `if/else`', 'sort_order': 1},
            {'label': 'Conversão de entradas numéricas', 'sort_order': 2},
        ],
    },
    {
        'slug': 'listas-dicionarios-e-tuplas',
        'module_slug': 'logica-de-programacao-com-python',
        'category_slug': 'estruturas-e-algoritmos',
        'name': 'Listas, dicionários e tuplas',
        'description': 'Coleções fundamentais para agrupar, percorrer e organizar dados.',
        'goal': 'Manipular coleções básicas e usá-las em problemas simples.',
        'level_label': 'Coleções',
        'concept_kicker': 'Estruturas de dados básicas',
        'milestone_title': 'Checkpoint de coleções',
        'milestone_summary': 'Consolida percursos, busca simples e organização de dados em memória.',
        'milestone_requirement_label': 'Completar os exercícios principais da trilha.',
        'sort_order': 5,
        'concepts': [
            {'title': 'Percurso de coleção', 'summary': 'Navegar por listas e estruturas compostas com clareza.', 'why_it_matters': 'É o passo natural depois de dominar laços simples.', 'common_mistake': 'Confundir índice com valor.', 'sort_order': 1},
        ],
        'prerequisites': [
            {'label': 'Laços com `for` e `while`', 'sort_order': 1},
        ],
    },
    {
        'slug': 'strings-e-formatacao',
        'module_slug': 'logica-de-programacao-com-python',
        'category_slug': 'estruturas-e-algoritmos',
        'name': 'Strings e formatação',
        'description': 'Manipulação de texto, busca, limpeza e formatação de saída.',
        'goal': 'Trabalhar com strings com precisão e gerar saída controlada.',
        'level_label': 'Texto',
        'concept_kicker': 'Tratamento textual',
        'milestone_title': 'Checkpoint textual',
        'milestone_summary': 'Consolida operações de texto e saída formatada.',
        'milestone_requirement_label': 'Completar os exercícios de string e formatação.',
        'sort_order': 6,
        'concepts': [
            {'title': 'Normalização de texto', 'summary': 'Limpar, cortar e comparar strings.', 'why_it_matters': 'Evita falhas de validação e formatação.', 'common_mistake': 'Comparar texto sem tratar espaços/capitalização.', 'sort_order': 1},
        ],
        'prerequisites': [
            {'label': 'Entrada de dados com `input()`', 'sort_order': 1},
        ],
    },
    {
        'slug': 'funcoes-e-modularizacao',
        'module_slug': 'logica-de-programacao-com-python',
        'category_slug': 'estruturas-e-algoritmos',
        'name': 'Funções e modularização',
        'description': 'Decomposição de problemas, parâmetros, retorno e reaproveitamento.',
        'goal': 'Separar responsabilidades e reutilizar lógica de forma limpa.',
        'level_label': 'Modularização',
        'concept_kicker': 'Decomposição',
        'milestone_title': 'Checkpoint de funções',
        'milestone_summary': 'Consolida parâmetros, retorno e extração de comportamento.',
        'milestone_requirement_label': 'Completar os exercícios principais da trilha.',
        'sort_order': 7,
        'concepts': [
            {'title': 'Funções com responsabilidade clara', 'summary': 'Encapsular uma regra ou cálculo em bloco reutilizável.', 'why_it_matters': 'É a porta de entrada para código mais organizado.', 'common_mistake': 'Criar funções que só mudam nome sem reduzir complexidade.', 'sort_order': 1},
        ],
        'prerequisites': [
            {'label': 'Condicionais e repetições básicas', 'sort_order': 1},
        ],
    },
    {
        'slug': 'arquivos-e-persistencia',
        'module_slug': 'logica-de-programacao-com-python',
        'category_slug': 'persistencia-e-modelagem',
        'name': 'Arquivos e persistência',
        'description': 'Leitura, escrita e processamento simples de arquivos.',
        'goal': 'Entender persistência básica antes de banco de dados.',
        'level_label': 'Persistência',
        'concept_kicker': 'Entrada e saída persistida',
        'milestone_title': 'Checkpoint de arquivos',
        'milestone_summary': 'Consolida leitura, escrita e transformação de dados persistidos.',
        'milestone_requirement_label': 'Completar os exercícios-base da trilha.',
        'sort_order': 8,
        'concepts': [
            {'title': 'Fluxo de leitura/escrita', 'summary': 'Entrar, transformar e persistir dados em arquivo.', 'why_it_matters': 'Prepara o aluno para pensar além do terminal.', 'common_mistake': 'Misturar processamento e persistência sem separar passos.', 'sort_order': 1},
        ],
        'prerequisites': [
            {'label': 'Strings e coleções básicas', 'sort_order': 1},
        ],
    },
    {
        'slug': 'classes-objetos-e-sqlite',
        'module_slug': 'logica-de-programacao-com-python',
        'category_slug': 'persistencia-e-modelagem',
        'name': 'Classes, objetos e SQLite',
        'description': 'Primeiros passos de modelagem orientada a objetos e persistência relacional simples.',
        'goal': 'Conectar modelagem de objetos com persistência básica em banco.',
        'level_label': 'Modelagem',
        'concept_kicker': 'Estado mais rico',
        'milestone_title': 'Checkpoint de modelagem',
        'milestone_summary': 'Integra representação de domínio e persistência simples.',
        'milestone_requirement_label': 'Completar os exercícios principais da trilha.',
        'sort_order': 9,
        'concepts': [
            {'title': 'Objeto como representação de domínio', 'summary': 'Organizar dados e comportamento em torno de uma entidade.', 'why_it_matters': 'Ajuda a pensar sistemas mais amplos.', 'common_mistake': 'Criar classe sem responsabilidade real.', 'sort_order': 1},
        ],
        'prerequisites': [
            {'label': 'Funções e modularização', 'sort_order': 1},
        ],
    },
    {
        'slug': 'fundamentos-de-api-com-fastapi',
        'module_slug': 'desenvolvimento-web-com-fastapi',
        'category_slug': 'web-backend',
        'name': 'Fundamentos de API com FastAPI',
        'description': 'Scaffold inicial para rotas, métodos HTTP e respostas JSON.',
        'goal': 'Preparar a base do módulo FastAPI.',
        'level_label': 'Scaffold',
        'concept_kicker': 'HTTP básico',
        'milestone_title': 'Checkpoint de API',
        'milestone_summary': 'Trilha reservada para a primeira rodada prática de FastAPI.',
        'milestone_requirement_label': 'Conteúdo em preparação.',
        'sort_order': 1,
        'concepts': [],
        'prerequisites': [],
    },
    {
        'slug': 'rotas-validacao-e-servicos',
        'module_slug': 'desenvolvimento-web-com-fastapi',
        'category_slug': 'web-backend',
        'name': 'Rotas, validação e serviços',
        'description': 'Scaffold inicial para contratos, validação e organização em camadas.',
        'goal': 'Preparar a base intermediária do módulo FastAPI.',
        'level_label': 'Scaffold',
        'concept_kicker': 'Contrato e serviço',
        'milestone_title': 'Checkpoint backend',
        'milestone_summary': 'Trilha reservada para evolução futura.',
        'milestone_requirement_label': 'Conteúdo em preparação.',
        'sort_order': 2,
        'concepts': [],
        'prerequisites': [],
    },
    {
        'slug': 'componentes-e-estado-com-vue',
        'module_slug': 'desenvolvimento-frontend-com-vue',
        'category_slug': 'frontend-moderno',
        'name': 'Componentes e estado com Vue',
        'description': 'Scaffold inicial para composição de interface e reatividade.',
        'goal': 'Preparar a base do módulo Vue.',
        'level_label': 'Scaffold',
        'concept_kicker': 'Interface e estado',
        'milestone_title': 'Checkpoint de componentes',
        'milestone_summary': 'Trilha reservada para evolução futura.',
        'milestone_requirement_label': 'Conteúdo em preparação.',
        'sort_order': 1,
        'concepts': [],
        'prerequisites': [],
    },
    {
        'slug': 'consumo-de-api-e-ux',
        'module_slug': 'desenvolvimento-frontend-com-vue',
        'category_slug': 'frontend-moderno',
        'name': 'Consumo de API e UX',
        'description': 'Scaffold inicial para integração com backend e estados de interface.',
        'goal': 'Preparar a segunda faixa do módulo Vue.',
        'level_label': 'Scaffold',
        'concept_kicker': 'Integração de interface',
        'milestone_title': 'Checkpoint de UX',
        'milestone_summary': 'Trilha reservada para evolução futura.',
        'milestone_requirement_label': 'Conteúdo em preparação.',
        'sort_order': 2,
        'concepts': [],
        'prerequisites': [],
    },
    {
        'slug': 'contratos-e-integracao-http',
        'module_slug': 'integracao-full-stack',
        'category_slug': 'integracao-de-sistemas',
        'name': 'Contratos e integração HTTP',
        'description': 'Scaffold inicial para contratos, payloads e integração entre camadas.',
        'goal': 'Preparar a base da integração full-stack.',
        'level_label': 'Scaffold',
        'concept_kicker': 'Contrato entre sistemas',
        'milestone_title': 'Checkpoint de integração',
        'milestone_summary': 'Trilha reservada para evolução futura.',
        'milestone_requirement_label': 'Conteúdo em preparação.',
        'sort_order': 1,
        'concepts': [],
        'prerequisites': [],
    },
    {
        'slug': 'fluxos-end-to-end',
        'module_slug': 'integracao-full-stack',
        'category_slug': 'integracao-de-sistemas',
        'name': 'Fluxos end-to-end',
        'description': 'Scaffold inicial para casos integradores entre frontend e backend.',
        'goal': 'Preparar exercícios que conectem múltiplas camadas.',
        'level_label': 'Scaffold',
        'concept_kicker': 'Percurso completo',
        'milestone_title': 'Checkpoint full-stack',
        'milestone_summary': 'Trilha reservada para evolução futura.',
        'milestone_requirement_label': 'Conteúdo em preparação.',
        'sort_order': 2,
        'concepts': [],
        'prerequisites': [],
    },
    {
        'slug': 'fundamentos-java-17',
        'module_slug': 'preparatorio-ocp-17',
        'category_slug': 'certificacoes',
        'name': 'Fundamentos Java 17',
        'description': 'Scaffold inicial para sintaxe, fluxo e regras-base da certificação.',
        'goal': 'Preparar a base do módulo OCP 17.',
        'level_label': 'Exam prep',
        'concept_kicker': 'Base da certificação',
        'milestone_title': 'Checkpoint Java',
        'milestone_summary': 'Trilha reservada para preparação futura.',
        'milestone_requirement_label': 'Conteúdo em preparação.',
        'sort_order': 1,
        'concepts': [],
        'prerequisites': [],
    },
    {
        'slug': 'simulados-ocp-17',
        'module_slug': 'preparatorio-ocp-17',
        'category_slug': 'certificacoes',
        'name': 'Simulados OCP 17',
        'description': 'Scaffold inicial para exercícios exam-like e simulados curtos.',
        'goal': 'Preparar a camada de prática orientada a certificação.',
        'level_label': 'Exam prep',
        'concept_kicker': 'Exam-like',
        'milestone_title': 'Checkpoint exam-like',
        'milestone_summary': 'Trilha reservada para evolução futura.',
        'milestone_requirement_label': 'Conteúdo em preparação.',
        'sort_order': 2,
        'concepts': [],
        'prerequisites': [],
    },
]


EXERCISE_ASSIGNMENTS = {
    'soma-dois-inteiros': {'track_slug': 'variaveis-tipos-e-entrada-de-dados', 'exercise_type_slug': 'drill-de-implementacao', 'estimated_time_minutes': 10, 'track_position': 1, 'concept_summary': 'Leitura de inteiros e soma direta.', 'pedagogical_brief': 'Exercício-base para validar leitura, conversão e saída limpa.'},
    'area-triangulo': {'track_slug': 'variaveis-tipos-e-entrada-de-dados', 'exercise_type_slug': 'drill-de-implementacao', 'estimated_time_minutes': 12, 'track_position': 2, 'concept_summary': 'Float, fórmula e impressão do resultado.', 'pedagogical_brief': 'Treina aplicação direta de fórmula com entrada numérica.'},
    'fahrenheit-celsius': {'track_slug': 'variaveis-tipos-e-entrada-de-dados', 'exercise_type_slug': 'drill-de-implementacao', 'estimated_time_minutes': 12, 'track_position': 3, 'concept_summary': 'Conversão de temperatura com fórmula.', 'pedagogical_brief': 'Consolida aritmética e uso correto de float.'},
    'media-duas-notas': {'track_slug': 'condicoes', 'exercise_type_slug': 'checkpoint-de-trilha', 'estimated_time_minutes': 15, 'track_position': 1, 'concept_summary': 'Cálculo seguido por decisão condicional.', 'pedagogical_brief': 'Questão clássica de prova que combina média e classificação.'},
    'maior-ou-igual-cem': {'track_slug': 'condicoes', 'exercise_type_slug': 'drill-de-implementacao', 'estimated_time_minutes': 10, 'track_position': 2, 'concept_summary': 'Comparação simples com dois caminhos.', 'pedagogical_brief': 'Treina if/else direto sem ruído.'},
    'calculadora-somar-subtrair': {'track_slug': 'condicoes', 'exercise_type_slug': 'implementacao-guiada', 'estimated_time_minutes': 12, 'track_position': 3, 'concept_summary': 'Menu simples com decisão por opção.', 'pedagogical_brief': 'Introduz escolha de operação com condicional.'},
    'par-ou-impar': {'track_slug': 'condicoes', 'exercise_type_slug': 'drill-de-implementacao', 'estimated_time_minutes': 10, 'track_position': 4, 'concept_summary': 'Uso de módulo e decisão binária.', 'pedagogical_brief': 'Problema objetivo para consolidar teste com resto da divisão.'},
    'maior-de-dois': {'track_slug': 'condicoes', 'exercise_type_slug': 'drill-de-implementacao', 'estimated_time_minutes': 10, 'track_position': 5, 'concept_summary': 'Comparação entre dois valores.', 'pedagogical_brief': 'Treina prioridade entre casos e tratamento de igualdade.'},
    'positivo-nulo-negativo': {'track_slug': 'condicoes', 'exercise_type_slug': 'drill-de-implementacao', 'estimated_time_minutes': 10, 'track_position': 6, 'concept_summary': 'Classificação em três cenários.', 'pedagogical_brief': 'Consolida cadeia de decisão com if/elif/else.'},
    'lucro-ou-prejuizo': {'track_slug': 'condicoes', 'exercise_type_slug': 'implementacao-guiada', 'estimated_time_minutes': 12, 'track_position': 7, 'concept_summary': 'Comparação entre compra e venda.', 'pedagogical_brief': 'Aplica três cenários de negócio em um fluxo simples.'},
    'idade-para-votar': {'track_slug': 'condicoes', 'exercise_type_slug': 'checkpoint-de-trilha', 'estimated_time_minutes': 12, 'track_position': 8, 'concept_summary': 'Mistura cálculo e regra condicional.', 'pedagogical_brief': 'Exercício de consolidação entre fórmula e decisão.'},
    'contar-numeros-flag': {'track_slug': 'repeticoes', 'exercise_type_slug': 'drill-de-implementacao', 'estimated_time_minutes': 15, 'track_position': 1, 'concept_summary': 'Loop com sentinela e contador.', 'pedagogical_brief': 'Base para problemas de while com flag de parada.'},
    'media-turma-flag': {'track_slug': 'repeticoes', 'exercise_type_slug': 'checkpoint-de-trilha', 'estimated_time_minutes': 18, 'track_position': 2, 'concept_summary': 'Laço com soma e contador para média.', 'pedagogical_brief': 'Consolida repetição com estado acumulado.'},
    'media-dos-pares': {'track_slug': 'repeticoes', 'exercise_type_slug': 'checkpoint-de-trilha', 'estimated_time_minutes': 18, 'track_position': 3, 'concept_summary': 'Filtro condicional dentro do laço.', 'pedagogical_brief': 'Mistura módulo, repetição, contador e acumulador.'},
    'menor-valor-flag': {'track_slug': 'repeticoes', 'exercise_type_slug': 'drill-de-implementacao', 'estimated_time_minutes': 16, 'track_position': 4, 'concept_summary': 'Atualização de menor valor durante o loop.', 'pedagogical_brief': 'Treina acumulador mínimo com sentinela.'},
    'menor-e-maior-valor': {'track_slug': 'repeticoes', 'exercise_type_slug': 'checkpoint-de-trilha', 'estimated_time_minutes': 18, 'track_position': 5, 'concept_summary': 'Dois acumuladores em paralelo.', 'pedagogical_brief': 'Consolida rastreamento de extremos em repetição.'},
    'altura-e-genero': {'track_slug': 'repeticoes', 'exercise_type_slug': 'checkpoint-de-trilha', 'estimated_time_minutes': 20, 'track_position': 6, 'concept_summary': 'Leitura contínua com múltiplos acumuladores.', 'pedagogical_brief': 'Problema mais rico de repetição e classificação.'},
    'naturais-vertical-ate-10': {'track_slug': 'repeticoes', 'exercise_type_slug': 'drill-de-implementacao', 'estimated_time_minutes': 10, 'track_position': 7, 'concept_summary': 'Sequência simples com for.', 'pedagogical_brief': 'Introduz repetição determinística com range.'},
    'naturais-pares-ate-12': {'track_slug': 'repeticoes', 'exercise_type_slug': 'drill-de-implementacao', 'estimated_time_minutes': 10, 'track_position': 8, 'concept_summary': 'Geração de pares com range.', 'pedagogical_brief': 'Consolida limites e passo em sequência conhecida.'},
    'naturais-impares-ate-13': {'track_slug': 'repeticoes', 'exercise_type_slug': 'drill-de-implementacao', 'estimated_time_minutes': 10, 'track_position': 9, 'concept_summary': 'Geração de ímpares com range.', 'pedagogical_brief': 'Consolida laço `for` e filtragem por módulo.'},
    'multiplos-de-tres-ate-21': {'track_slug': 'repeticoes', 'exercise_type_slug': 'drill-de-implementacao', 'estimated_time_minutes': 12, 'track_position': 10, 'concept_summary': 'Iteração com regra modular.', 'pedagogical_brief': 'Exercício objetivo para treinar sequências com critério.'},
    'ordem-decrescente-7-1': {'track_slug': 'repeticoes', 'exercise_type_slug': 'drill-de-implementacao', 'estimated_time_minutes': 10, 'track_position': 11, 'concept_summary': 'Range com passo negativo.', 'pedagogical_brief': 'Mostra direção decrescente explicitamente.'},
    'sequencia-inteiros-intervalo': {'track_slug': 'repeticoes', 'exercise_type_slug': 'implementacao-guiada', 'estimated_time_minutes': 14, 'track_position': 12, 'concept_summary': 'Percurso entre limites informados.', 'pedagogical_brief': 'Treina adaptação do laço à entrada do usuário.'},
    'sequencia-crescente-ou-decrescente': {'track_slug': 'repeticoes', 'exercise_type_slug': 'checkpoint-de-trilha', 'estimated_time_minutes': 16, 'track_position': 13, 'concept_summary': 'Escolha dinâmica de direção do laço.', 'pedagogical_brief': 'Consolida for com decisão sobre sentido do intervalo.'},
    'media-turma-for': {'track_slug': 'repeticoes', 'exercise_type_slug': 'checkpoint-de-trilha', 'estimated_time_minutes': 16, 'track_position': 14, 'concept_summary': 'Média baseada em quantidade fixa de entradas.', 'pedagogical_brief': 'Fecha a trilha de repetição com for e acumulador.'},
}


def seed_catalog(apps, schema_editor):
    Exercise = apps.get_model('arena', 'Exercise')
    ExerciseCategory = apps.get_model('arena', 'ExerciseCategory')
    ExerciseTrack = apps.get_model('arena', 'ExerciseTrack')
    ExerciseType = apps.get_model('arena', 'ExerciseType')
    LearningModule = apps.get_model('arena', 'LearningModule')
    ExerciseTrackConcept = apps.get_model('arena', 'ExerciseTrackConcept')
    ExerciseTrackPrerequisite = apps.get_model('arena', 'ExerciseTrackPrerequisite')
    ExerciseExplanation = apps.get_model('arena', 'ExerciseExplanation')

    for exercise_type_data in EXERCISE_TYPES:
        ExerciseType.objects.update_or_create(
            slug=exercise_type_data['slug'],
            defaults={
                'name': exercise_type_data['name'],
                'description': exercise_type_data['description'],
                'sort_order': exercise_type_data['sort_order'],
            },
        )

    for category_data in CATEGORIES:
        ExerciseCategory.objects.update_or_create(
            slug=category_data['slug'],
            defaults={
                'name': category_data['name'],
                'description': category_data['description'],
                'sort_order': category_data['sort_order'],
            },
        )

    module_lookup = {}
    for module_data in MODULES:
        module, _ = LearningModule.objects.update_or_create(
            slug=module_data['slug'],
            defaults={
                'name': module_data['name'],
                'description': module_data['description'],
                'audience': module_data['audience'],
                'source_kind': module_data['source_kind'],
                'status': module_data['status'],
                'sort_order': module_data['sort_order'],
            },
        )
        module_lookup[module.slug] = module

    for track_data in TRACKS:
        category = ExerciseCategory.objects.get(slug=track_data['category_slug'])
        module = module_lookup[track_data['module_slug']]
        track, _ = ExerciseTrack.objects.update_or_create(
            slug=track_data['slug'],
            defaults={
                'module': module,
                'category': category,
                'name': track_data['name'],
                'description': track_data['description'],
                'goal': track_data['goal'],
                'level_label': track_data['level_label'],
                'concept_kicker': track_data['concept_kicker'],
                'milestone_title': track_data['milestone_title'],
                'milestone_summary': track_data['milestone_summary'],
                'milestone_requirement_label': track_data['milestone_requirement_label'],
                'sort_order': track_data['sort_order'],
            },
        )
        ExerciseTrackConcept.objects.filter(track=track).delete()
        ExerciseTrackConcept.objects.bulk_create(
            [
                ExerciseTrackConcept(
                    track=track,
                    title=concept['title'],
                    summary=concept['summary'],
                    why_it_matters=concept['why_it_matters'],
                    common_mistake=concept['common_mistake'],
                    sort_order=concept['sort_order'],
                )
                for concept in track_data['concepts']
            ]
        )
        ExerciseTrackPrerequisite.objects.filter(track=track).delete()
        ExerciseTrackPrerequisite.objects.bulk_create(
            [
                ExerciseTrackPrerequisite(
                    track=track,
                    label=prerequisite['label'],
                    sort_order=prerequisite['sort_order'],
                )
                for prerequisite in track_data['prerequisites']
            ]
        )

    for exercise_slug, assignment in EXERCISE_ASSIGNMENTS.items():
        track = ExerciseTrack.objects.get(slug=assignment['track_slug'])
        exercise_type = ExerciseType.objects.get(slug=assignment['exercise_type_slug'])
        Exercise.objects.filter(slug=exercise_slug).update(
            category=track.category,
            track=track,
            exercise_type=exercise_type,
            estimated_time_minutes=assignment['estimated_time_minutes'],
            track_position=assignment['track_position'],
            concept_summary=assignment['concept_summary'],
            pedagogical_brief=assignment['pedagogical_brief'],
        )

    ExerciseExplanation.objects.all().delete()


def unseed_catalog(apps, schema_editor):
    ExerciseTrack = apps.get_model('arena', 'ExerciseTrack')
    LearningModule = apps.get_model('arena', 'LearningModule')
    ExerciseType = apps.get_model('arena', 'ExerciseType')
    Exercise = apps.get_model('arena', 'Exercise')

    Exercise.objects.update(
        exercise_type=None,
        track_position=0,
        concept_summary='',
        pedagogical_brief='',
    )
    ExerciseTrack.objects.filter(slug__in=[track['slug'] for track in TRACKS]).delete()
    LearningModule.objects.filter(slug__in=[module['slug'] for module in MODULES]).delete()
    ExerciseType.objects.filter(slug__in=[exercise_type['slug'] for exercise_type in EXERCISE_TYPES]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('arena', '0010_exercisetype_learningmodule_and_more'),
    ]

    operations = [
        migrations.RunPython(seed_catalog, unseed_catalog),
    ]
