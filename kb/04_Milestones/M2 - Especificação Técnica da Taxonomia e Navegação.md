# M2 - Especificação Técnica da Taxonomia e Navegação

## Objetivo desta nota

Traduzir a `M2` em uma sequência implementável e em um escopo fechável.

## O que já está pronto na base

Hoje o sistema já possui:

- `ExerciseCategory`
- `ExerciseTrack`
- `Exercise.category`
- `Exercise.track`
- seed inicial com classificação do catálogo
- API retornando `category_*` e `track_*`
- agrupamento visual por categoria na sidebar

Isso é uma boa fundação, mas ainda não é a solução completa da milestone.

## O que falta para a M2 ficar “de pé”

### 1. Navegação explícita por taxonomia

Hoje a arena só agrupa exercícios por categoria. Falta transformar isso numa navegação realmente orientada à taxonomia.

Isso pode ser feito com uma destas abordagens:

#### Abordagem A — rail hierárquico

- categoria como cabeçalho
- trilhas como subgrupos colapsáveis
- exercícios dentro de cada trilha

#### Abordagem B — filtros + lista

- filtro por categoria
- filtro por trilha
- lista de exercícios refinada dinamicamente

#### Recomendação

Para o estado atual do produto, eu adotaria um híbrido:

- agrupamento hierárquico na lateral
- filtros leves no topo do catálogo

Isso preserva simplicidade e já melhora muito a descoberta.

## 2. Metadados mínimos adicionais no domínio

Para a navegação deixar de ser apenas estrutural e passar a ser pedagógica, o modelo deveria ganhar ao menos:

### `exercise_type`

Valores possíveis na primeira versão:

- `core_drill`
- `exam_simulation`
- `guided_build`
- `integrative_case`

Esses valores são mais úteis do que rótulos vagos como `practice`, porque comunicam melhor a intenção pedagógica e o tipo de experiência esperada.

### `estimated_time_minutes`

Ajuda a comunicar tamanho do esforço e prepara melhor a gamificação/planejamento.

### `sort_order`

Dentro da trilha, a ordem não deve depender só do título.

### `is_recommended_start`

Opcional, mas muito útil para trilhas com ponto de entrada claro.

## 3. API mais adequada para navegação

Hoje a API já devolve taxonomia embutida por exercício. Isso é bom, mas ainda insuficiente para uma navegação canônica madura.

### Evoluções recomendadas

#### Opção mínima

Adicionar filtros em `GET /api/exercises/`:

- `category_slug`
- `track_slug`
- `difficulty`

#### Opção melhor

Criar também um endpoint de catálogo estruturado, como:

- `GET /api/exercise-catalog`

Resposta sugerida:

```json
[
  {
    "category_slug": "fundamentos",
    "category_name": "Fundamentos",
    "tracks": [
      {
        "track_slug": "condicionais-basicas",
        "track_name": "Condicionais Básicas",
        "exercise_count": 8,
        "exercises": [...]
      }
    ]
  }
]
```

### Recomendação

Para fechar a `M2` com elegância, o endpoint de catálogo estruturado é melhor do que depender só de agrupamento no frontend.

## 4. UX alvo para fechamento adequado da M2

Uma `M2` bem concluída precisa permitir que o usuário:

- veja categorias e trilhas com clareza;
- entenda a posição do exercício atual no mapa;
- filtre rapidamente o catálogo;
- saiba qual trilha está fazendo;
- perceba o próximo passo natural.

## 4.1 Leitura mais madura de `exercise_type`

### Por que o desenho anterior era raso

Tipos como:

- `exam_like`
- `practice`
- `integrative`

até apontam direções, mas continuam amplos demais. Eles não ajudam muito a decidir:

- qual UI usar;
- qual tom de ajuda oferecer;
- quanto guidance mostrar;
- qual expectativa de esforço comunicar.

### Proposta refinada de primeiros valores

#### `core_drill`

Exercício curto, objetivo, focado em uma habilidade central.

Exemplos:

- entrada e saída
- conversão
- condição simples
- laço curto

Experiência esperada:

- resolução rápida;
- pouco contexto extra;
- ideal para aquecimento e treino concentrado.

#### `exam_simulation`

Exercício que emula mais diretamente o estilo de prova do professor.

Experiência esperada:

- ambiente mais seco;
- menos ajuda;
- sensação mais forte de avaliação;
- destaque para formato de entrada e saída.

#### `guided_build`

Exercício que ainda é de prática, mas comporta scaffold mental mais claro, hints mais estratégicos e leitura em etapas.

Experiência esperada:

- pode ter subobjetivos;
- pode mostrar checklist da solução;
- serve bem para construir repertório sem virar tutorial demais.

#### `integrative_case`

Desafio mais amplo, que integra várias peças de raciocínio ou até várias camadas do sistema.

Experiência esperada:

- leitura mais longa;
- maior tempo estimado;
- trilha mais avançada;
- maior peso na percepção de domínio.

### Conclusão

Esses quatro tipos iniciais já são suficientes para orientar UI, copy, dificuldade percebida e evolução do catálogo sem criar tipologia demais cedo.

## 5. Checklist de fechamento realista

### Backend

- modelos com taxonomia mínima estável
- seed todo classificado
- nenhum exercício órfão
- filtros no endpoint ou catálogo estruturado

### Frontend

- navegação por categoria e trilha
- filtros básicos
- estado visual do exercício atual dentro da trilha
- caminho sugerido de progressão
- tratamento visual coerente para pelo menos os primeiros `exercise_type`

### Conteúdo

- taxonomia revisada com coerência pedagógica
- ordem dos exercícios definida dentro de cada trilha

## 6. O que eu considero “fora da M2”

Para não inflar a milestone além do necessário, eu não colocaria aqui:

- achievements
- ranking
- mastery scoring
- badges
- desafios full-stack

Esses pontos dependem da `M2`, mas pertencem a outras milestones.

## Sequência recomendada para completar a M2

1. adicionar metadados mínimos faltantes no domínio
2. expor filtro/catálogo estruturado na API
3. refinar `exercise_type` e seus primeiros valores
4. refazer a navegação lateral para categoria + trilha
5. adicionar filtros básicos
6. comunicar ordem recomendada de progressão
7. revisar seed e classificação final

## Próxima leitura

- [[M2 - Navegação Autenticada e Tipos de Exercício]]

## Conclusão operacional

Se a pergunta é “o que falta para a tarefa estar realmente concluída no escopo da `M2`?”, a resposta curta é:

**falta transformar taxonomia em navegação pedagógica de verdade**.

Hoje a taxonomia existe. O que ainda não existe plenamente é a experiência canônica baseada nela.

## Atualização de implementação - 2026-04-11

A `M2` deixou de ser apenas direção conceitual e ganhou uma primeira fatia real no produto.

### O que entrou no backend

- nova camada `arena/catalog.py` com metadados editoriais por trilha;
- enriquecimento do resumo de exercício com:
  - `exercise_type`
  - `exercise_type_label`
  - `estimated_time_minutes`
  - `concept_summary`
- novo endpoint autenticado `GET /api/catalog/navigator`
- novo endpoint autenticado `GET /api/catalog/tracks/{track_slug}`

### O que esses endpoints resolvem

O catálogo não precisa mais ser reconstruído inteiramente no frontend a partir de uma lista plana de exercícios.

Agora o backend já devolve:

- categorias com trilhas agregadas;
- progresso por trilha;
- `current_target` por trilha;
- roadmap de exercícios com estado:
  - `passed`
  - `in_progress`
  - `available`
  - `locked`
- milestone/checkpoint da trilha;
- conceitos e pré-requisitos editoriais da trilha.

### O que entrou no frontend

- nova rota autenticada `Navigator`
- nova rota autenticada `Track`
- redirecionamento pós-login para `Navigator`
- arena aceitando contexto via query string:
  - `exercise`
  - `track`
- rail lateral da arena ficando contextual quando aberta a partir de uma trilha

### Leitura honesta desta fatia

Essa implementação **não fecha toda a M2**, mas muda o estado da milestone de forma importante:

- já existe uma superfície real de descoberta (`Navigator`);
- já existe uma superfície real de progressão (`Track Page`);
- a arena já começou a respeitar contexto de trilha;
- a plataforma já comunica melhor tipos de exercício, tempo estimado e target atual.

### O que ainda ficou para a próxima fatia

- persistir os metadados novos no domínio, em vez de depender de catálogo editorial em código;
- modelar explicitamente a camada de `Concept` e explicações reaproveitáveis;
- adicionar filtros de verdade no `Navigator`;
- aprofundar a ligação entre `Track Page`, documentação e Arena;
- refinar a ordem pedagógica com `sort_order` explícito por exercício.

### Refinamento de UX na segunda rodada

Depois da primeira materialização, a navegação ganhou uma segunda revisão importante:

- o catálogo e a trilha passaram a oferecer botões mais diretos de ida e volta entre superfícies;
- o roadmap da trilha foi reorganizado para parecer mais com um caminho do que com uma lista;
- a Arena passou a expor atalhos contextuais para `Navigator`, `Track` e navegação entre steps;
- o seletor de tema foi exposto na UI autenticada, consolidando uma direção de personalização simples e uniforme.

Essa camada não altera a tese da `M2`; ela apenas deixa a experiência menos frágil na prática.

## Ajuste de navegação - 2026-04-11

A segunda rodada de refinamento começou a atacar a fricção que sobrou na ida e volta entre superfícies:

- a `Track Page` agora opera mais como mapa do que como lista vertical;
- os steps seguem a sequência pedagógica dos módulos, e não a ordem casual do banco;
- a `Arena` ganhou atalhos explícitos para `Navigator`, `Track Roadmap` e `Próxima etapa`;
- o rail lateral continua contextual quando a arena é aberta a partir de uma trilha.

Isso aproxima bastante a experiência do fluxo ideal que queríamos para a `M2`.
