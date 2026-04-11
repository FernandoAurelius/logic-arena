# M2 - Taxonomia e Navegação Canônica

## Problema

O catálogo já começou a crescer, mas a navegação ainda é muito próxima de uma lista simples de exercícios.

## Objetivo

Transformar o banco de exercícios em uma estrutura navegável por categoria, assunto, trilha e dificuldade.

## Resultado esperado

- catálogo navegável por camadas;
- exercícios organizados por progressão;
- UX mais clara para aluno novo e para aluno avançado;
- base para mastery e ranking por domínio.

## Modelo sugerido

Adicionar ao domínio conceitos como:

- `Category`
- `Topic`
- `Track`
- `ExerciseType`
- `estimated_time`
- `learning_goals`

## Interpretação correta do escopo da M2

A `M2` não é apenas “colocar categorias no banco”. Ela existe para resolver três problemas ao mesmo tempo:

1. dar forma canônica ao catálogo;
2. tornar a navegação previsível para catálogo crescente;
3. preparar a base semântica para `mastery`, ranking, achievements e expansão curricular.

Se a gente parar na modelagem mínima, a milestone fica só meio feita. A taxonomia nasce, mas a experiência do produto ainda não muda o suficiente.

## Domínio alvo da M2

### Camadas conceituais ideais

#### 1. Category

Camada mais ampla de organização.

Exemplos:

- `Fundamentos`
- `Controle de Fluxo`
- `Coleções e Estruturas`
- `Funções e Modularização`
- `Projetos Integradores`

#### 2. Track

Agrupamento navegável dentro da categoria, com começo, meio e fim percebidos.

Exemplos:

- `Entrada, Saída e Fórmulas`
- `Condicionais Básicas`
- `Flags e While`
- `Sequências e For`

#### 3. Topic ou Subtopic

Camada ainda não implementada, mas relevante para o futuro, especialmente quando o catálogo crescer ou quando começarem desafios mais complexos.

Essa camada pode ser introduzida depois sem invalidar o que já foi feito, desde que `Category` e `Track` continuem bem definidos.

#### 4. Metadados pedagógicos

Também não implementados ainda, mas parte do escopo ideal:

- `exercise_type`
- `estimated_time`
- `learning_goals`
- `is_exam_like`
- `prerequisites`

## Estado real implementado hoje

### Já existe

- `ExerciseCategory`
- `ExerciseTrack`
- vínculo de `Exercise` com categoria e trilha
- seed/backfill classificando os exercícios atuais
- API devolvendo `category_*` e `track_*`
- sidebar agrupando itens por categoria

### Ainda não existe

- filtro de catálogo por categoria
- filtro por trilha
- filtro por dificuldade
- visão “por trilha” em vez de apenas agrupamento visual
- progresso agregado por trilha
- recomendação explícita de “onde começar”
- distinção clara entre:
  - exercícios de prova
  - treino comum
  - desafios integradores

## Mudanças de frontend

- trocar lista plana lateral por navegação mais canônica;
- permitir filtros por categoria, assunto, dificuldade e status;
- manter leitura simples mesmo com catálogo maior.

### O que “navegação canônica” deve significar na prática

Não basta empilhar grupos. A navegação ideal da `M2` precisa permitir pelo menos:

- enxergar as categorias principais;
- enxergar trilhas dentro de cada categoria;
- perceber quantos exercícios existem em cada trilha;
- saber em que trilha o exercício atual está;
- filtrar o catálogo sem esforço;
- entender uma ordem sugerida de progressão.

Se isso não existir, o usuário continua navegando quase como lista plana, só que com títulos de grupo.

## Mudanças de conteúdo

- reclassificar o seed atual;
- mapear cada exercício a uma trilha;
- marcar quais exercícios são de prova e quais são integradores.

### Leitura importante

Conteúdo e navegação são a mesma discussão aqui. Se o catálogo for taxonomizado de forma superficial, o front também vai parecer superficial.

## Critério de aceite

Um usuário novo consegue entender com clareza:

- por onde começar;
- o que é fundamento vs desafio avançado;
- como avançar por trilhas em vez de clicar aleatoriamente.

## Critério de aceite mais operacional

Para considerar a `M2` adequadamente concluída dentro do escopo definido, eu usaria este checklist:

### Domínio

- `Category` e `Track` existem no backend
- todo exercício ativo está classificado
- a taxonomia atual não deixa itens órfãos

### API

- listagem de exercícios devolve taxonomia
- detalhe do exercício devolve taxonomia
- existe pelo menos uma forma de filtrar ou pedir o catálogo já segmentado

### Frontend

- a arena não apresenta mais o catálogo como pseudo-lista plana
- o usuário vê categoria e trilha do exercício atual
- existem filtros ou navegação explícita por taxonomia
- a UI comunica um caminho sugerido de progressão

### Produto

- um aluno novo entende onde começar
- um aluno intermediário entende como continuar
- a expansão futura do catálogo não exige reinventar a navegação

## Diagnóstico honesto do estado atual

Hoje a `M2` está **iniciada e parcialmente implementada**, mas **não concluída**.

### O que já resolveu

- saiu do zero semântico;
- eliminou a condição de catálogo completamente amorfo;
- deu base real para agrupamento e futuros relatórios de domínio.

### O que ainda impede chamar de “concluída”

- a navegação ainda não é realmente orientada a trilhas;
- faltam filtros;
- falta recomendação explícita de percurso;
- falta traduzir taxonomia em experiência pedagógica mais forte;
- o modelo ainda está mais perto de “classificação interna” do que de “navegação canônica madura”.

## Status da implementação

### Base já implementada

- `ExerciseCategory` e `ExerciseTrack` no domínio;
- `Exercise` ligado a categoria e trilha;
- seed/backfill inicial classificando o catálogo atual;
- API já devolvendo `category_*` e `track_*`;
- sidebar da arena deixando de ser uma lista totalmente plana e passando a agrupar exercícios por categoria.

### O que ainda falta

- filtros explícitos por categoria, trilha e dificuldade;
- ordenação e navegação por trilha como entidade de primeira classe;
- visualização de progresso por trilha;
- recomendação explícita de percurso;
- metadados pedagógicos mínimos para escalar o catálogo;
- separação futura entre exercícios de prova, prática livre e integradores;
- ampliação da taxonomia para novos tipos de exercício e categorias futuras.

## Próxima leitura

- [[M2 - Especificação Técnica da Taxonomia e Navegação]]
