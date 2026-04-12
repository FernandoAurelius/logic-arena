# M2 - Navegação Autenticada e Tipos de Exercício

## Objetivo desta nota

Refinar a parte da `M2` que estava mais vaga: como o usuário autenticado deve navegar pelo catálogo sem quebrar a autenticidade da arena, e como os tipos de exercício devem influenciar essa navegação e a experiência.

## Princípio de produto

O `Logic Arena` já tem uma shell forte e uma arena com identidade clara. Então a navegação nova não deve parecer um LMS genérico anexado ao lado. Ela precisa continuar parecendo uma estação de treino técnica.

Em outras palavras:

- o catálogo não deve matar a sensação de arena;
- a navegação não deve parecer dashboard corporativo;
- a descoberta do exercício deve continuar parecendo parte da própria interface operacional.

## Proposta de fluxo autenticado

### Superfícies

Dentro da área autenticada, o sistema deveria ter duas superfícies complementares:

#### 1. Arena

Continua sendo o lugar de resolver o exercício.

Responsabilidades:

- mostrar o desafio ativo;
- exibir specification, editor, console, feedback e revisão;
- permitir trocar de exercício de forma rápida.

#### 2. Navigator

Nova página autenticada e dedicada ao catálogo.

Responsabilidades:

- mostrar categorias e trilhas com clareza;
- ajudar o usuário a escolher o próximo desafio;
- comunicar tipo de exercício, dificuldade, tempo estimado e status;
- servir como mapa da KB prática da plataforma.

## Por que uma página dedicada faz sentido

Hoje a sidebar da arena é suficiente para alternar exercícios, mas não para explorar o catálogo com profundidade.

Uma página `Navigator` resolve isso melhor porque separa dois modos mentais:

- `modo resolver`
- `modo escolher o que praticar`

Sem essa separação, a arena acaba tentando ser editor, console, feedback e catálogo ao mesmo tempo.

## Fluxo recomendado

### Entrada principal

1. usuário faz login
2. o sistema entra por uma `Authenticated Home`
3. essa home pode redirecionar automaticamente para:
   - último exercício aberto, se existir contexto recente
   - ou `Navigator`, se o usuário ainda não tiver trilha atual clara

### Da home para o catálogo

O usuário entra no `Navigator` para responder uma pergunta prática:

> O que faz mais sentido eu praticar agora?

### Do catálogo para a arena

Ao escolher um exercício, o sistema abre a arena já contextualizada com:

- categoria
- trilha
- posição naquela trilha
- tipo do exercício
- tempo estimado

## Modelo de navegação na barra lateral

### Papel novo da sidebar da arena

A sidebar dentro da arena não deve ser o catálogo completo do sistema. Ela deve ser o **rail contextual** da sessão atual.

### O que ela deveria mostrar

#### Se o usuário abriu a arena a partir de uma trilha

Mostrar:

- categoria atual
- trilha atual
- exercícios daquela trilha
- destaque do exercício ativo
- navegação rápida para próximo/anterior

#### Se o usuário abriu a arena fora de contexto

Mostrar:

- seção compacta de categorias
- exercício atual
- botão forte para abrir `Navigator`

### Conclusão prática

A sidebar da arena deve virar mais **contextual e local**, enquanto o `Navigator` assume a descoberta mais ampla.

## Estrutura sugerida para a página Navigator

### Faixa superior

- saudação curta
- progresso geral do operador
- CTA principal:
  - `Continuar trilha`
  - `Explorar catálogo`

### Coluna ou faixa de filtros

- categoria
- trilha
- dificuldade
- tipo de exercício
- status:
  - não iniciado
  - em progresso
  - concluído

### Área principal

Exibição por categoria -> trilha -> exercícios.

Cada card de exercício deveria mostrar no mínimo:

- título
- dificuldade
- tipo
- tempo estimado
- status
- posição na trilha

### Bloco especial de orientação

Um pequeno painel que responda:

- `por onde começar`
- `o que continuar`
- `o que revisar`

Isso ajuda a plataforma a parecer inteligente sem depender de IA para tudo.

## Tipos de exercício e impacto na UI

### `core_drill`

Uso:

- fundamentos
- treino curto
- repetição de habilidade central

UI sugerida:

- badge discreta
- foco em rapidez
- CTA simples: `Praticar agora`

### `exam_simulation`

Uso:

- treino no estilo da prova
- pouco guidance
- ambiente mais seco

UI sugerida:

- badge forte de simulação
- menor ênfase em hints
- destaque para formato de I/O

### `guided_build`

Uso:

- construção orientada de repertório
- desafios que ainda se beneficiam de estrutura

UI sugerida:

- comunicar claramente objetivos
- permitir checklist visível
- hints mais aceitáveis

### `integrative_case`

Uso:

- desafios maiores
- integração de vários conceitos
- preparação para problemas reais

UI sugerida:

- card maior ou mais denso
- tempo estimado visível
- indicação clara de desafio avançado

## Primeiros valores sugeridos para o catálogo atual

### Fundamentos

- maioria dos exercícios atuais: `core_drill`
- alguns que simulam mais prova: `exam_simulation`

### Controle de fluxo

- drills simples de laço: `core_drill`
- médias/flags mais típicas de prova: `exam_simulation`

### Futuros desafios

- problemas com etapas: `guided_build`
- mini sistemas e integrações: `integrative_case`

## Critério de navegação autêntica

O sistema deve continuar parecendo uma estação de prática, não uma biblioteca com editor colado.

Isso significa:

- descoberta do exercício em uma superfície dedicada;
- execução em outra superfície dedicada;
- sidebar da arena com foco contextual;
- linguagem visual consistente entre catálogo e arena.

## O que falta para isso virar implementação

### Backend

- persistir `exercise_type`
- persistir `estimated_time_minutes`
- persistir `sort_order`
- filtros e/ou catálogo estruturado

### Frontend

- criar rota autenticada para `Navigator`
- redefinir papel da sidebar da arena
- adicionar filtros e cards por trilha
- mostrar tipo de exercício e tempo estimado

## Recomendação final

Se quisermos que a `M2` pareça realmente bem resolvida, o caminho mais forte é:

1. introduzir os primeiros `exercise_type` bem definidos
2. criar a página autenticada `Navigator`
3. transformar a sidebar da arena em rail contextual de trilha

Isso preserva autenticidade e melhora descoberta sem diluir a força da arena.

## Atualização de implementação - 2026-04-11

A direção acima começou a ser materializada diretamente na UI.

### Superfícies autenticadas já criadas

#### 1. `Navigator`

Responsabilidade implementada:

- listar categorias e trilhas em uma superfície dedicada;
- destacar trilha recomendada;
- comunicar:
  - progresso;
  - target atual;
  - objetivo da trilha;
  - status geral.

#### 2. `Track Page`

Responsabilidade implementada:

- mostrar o roadmap da trilha;
- mostrar o step atual;
- exibir milestone/checkpoint;
- exibir painel pedagógico à direita;
- conectar a trilha diretamente com a entrada na arena.

#### 3. `Arena` contextualizada

Quando a arena é aberta a partir de uma trilha:

- recebe `track` e `exercise` pela rota;
- tenta abrir diretamente o exercício-alvo;
- deixa a sidebar mais contextual à trilha escolhida.

### O que isso resolve do ponto de vista de produto

O usuário agora já consegue viver três modos mentais distintos:

- `escolher o que praticar` no `Navigator`;
- `entender a progressão` na `Track Page`;
- `resolver o exercício` na `Arena`.

Esse desmembramento já aproxima bastante o produto do modelo que queríamos para a `M2`.

### Limite atual da implementação

Ainda não temos uma camada de `Concept` persistida como entidade de domínio. Por enquanto, a `Track Page` usa um catálogo editorial em código para:

- conceitos;
- pré-requisitos;
- objetivos da trilha;
- metadados pedagógicos do step.

Isso é suficiente para validar UX e direção de produto, mas não é ainda o desenho final do domínio.

## Refinamento de UX - 2026-04-11

Depois da primeira entrega da `M2`, surgiram três ajustes claros de experiência:

- a ida e volta entre `Navigator`, `Track` e `Arena` ainda podia ficar mais fluida;
- a ordem dos módulos precisava respeitar melhor a sequência pedagógica da trilha;
- o roadmap ainda estava mais perto de lista vertical do que de mapa de progressão.

### O que foi refinado

- `Navigator` passou a oferecer não só entrada na trilha, mas também entrada direta na `Arena` já contextualizada;
- a `Track Page` ganhou um caminho mais próximo de mapa em zigue-zague, inspirado no `Architectural Roadmap`, em vez de apenas empilhar cards;
- a `Arena` ganhou breadcrumbs acionáveis, CTA para voltar ao roadmap e navegação entre etapa anterior/próxima;
- a sidebar da `Arena`, quando em contexto de trilha, passou a respeitar melhor a ordem dos steps;
- a plataforma recebeu uma camada isolada de microinterações;
- a plataforma recebeu base para múltiplos temas de cor e um seletor reutilizável de tema.

### Leitura correta desta rodada

A `M2` agora não é mais só uma hipótese de catálogo melhorado. Ela já tem:

- descoberta;
- progressão;
- fluxo de retorno;
- base visual mais viva;
- começo de personalização de experiência.

O próximo passo natural continua sendo persistir melhor a camada de conceitos e metadados editoriais no domínio, mas a experiência já começou a parecer produto real.

### Ajuste de navegação e mapa visual - 2026-04-11

A ergonomia da trilha foi refinada para ficar menos “lista vertical” e mais “mapa de percurso”.

#### O que mudou

- a trilha passou a ordenar os módulos por uma sequência editorial explícita;
- a visualização dos steps passou a alternar lados, com linha central regular, para parecer mais com um caminho navegável;
- o detalhe do step ganhou botões de etapa anterior/próxima, além de atalhos diretos para a Arena e para o Navigator;
- a superfície `Navigator` passou a oferecer também uma entrada direta na Arena com o contexto da trilha atual;
- a Arena já expõe ações rápidas para voltar ao `Navigator`, abrir o `Track Roadmap` e avançar entre exercícios do percurso.

#### O que ainda pode evoluir depois

- transformar o roadmap em uma grade ainda mais orgânica, com checkpoints intermediários e ramificações;
- persistir a ordem da trilha no domínio em vez de depender apenas do catálogo editorial;
- adicionar filtros mais finos no Navigator sem perder a estética operacional;
- conectar melhor cada step a uma nota de conceito ou explicação reaproveitável.

## Ajuste de navegação - 2026-04-11

O fluxo ficou mais fluido na segunda rodada:

- o roadmap da trilha ganhou uma forma mais próxima de mapa/jornada;
- o step atual passou a abrir com mais precisão a próxima ação;
- a arena passou a expor atalhos claros de retorno para a trilha e para o Navigator;
- a ordenação dos módulos agora respeita a sequência pedagógica dos steps.

Essa foi uma correção importante porque transformou a navegação em algo mais operável no dia a dia, e não apenas bonito.

## Explanation como domínio persistido - 2026-04-11

Uma correção importante desta rodada foi parar de tratar `Explanation` como montagem oportunista de frontend.

### O problema da abordagem anterior

Enquanto a tela de explanation fosse só uma composição local da view:

- ela não existiria como recurso real do produto;
- o frontend continuaria responsável por inventar estrutura pedagógica;
- exemplos de código correriam o risco de virar detalhe visual, e não parte obrigatória do conteúdo;
- a plataforma continuaria sem uma base sólida para evoluir explicações curadas no futuro.

### O que foi modelado

Entraram três entidades explícitas no backend:

- `ExerciseExplanation`
- `ExerciseExplanationConcept`
- `ExerciseExplanationCodeExample`

Isso transforma a explanation em agregado real do sistema, associado ao exercício e servido por endpoint próprio.

### Contrato novo da plataforma

O frontend agora consome um endpoint dedicado:

- `GET /api/catalog/tracks/{track_slug}/explanations/{exercise_slug}`

Esse recurso entrega:

- metadados da trilha;
- metadados do módulo;
- objetivo de aprendizagem;
- foco conceitual em Markdown;
- estratégia de leitura do problema;
- estratégia de implementação;
- notas de cobrança;
- lista de conceitos;
- exemplos de código obrigatórios.

### Decisão arquitetural consolidada

A leitura da explanation **não deve mais regerar conteúdo a cada acesso**.

O fluxo certo agora é:

1. seed ou cadastro do exercício materializa a explanation;
2. a API serve esse recurso persistido;
3. o frontend apenas apresenta.

Quando a explanation ainda não existir, ela pode ser criada sob demanda uma única vez. O ponto importante é que o acesso de leitura não reescreva o conteúdo toda vez.

### Impacto na M2

Isso não fecha a `M2` inteira, mas muda a qualidade da milestone:

- o `drawer` da trilha volta a ser apenas ponto de decisão;
- a `Explanation View` passa a ser uma página documental de verdade;
- a navegação por trilha já aponta para uma superfície pedagógica real, e não para texto improvisado da interface.
