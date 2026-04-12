# M4 - Catálogo Avançado e Projetos Integradores

## Estado atual da implementação

Em `2026-04-12`, a `M4` deixou de ser apenas desenho e passou a ter base funcional no código:

- o domínio agora possui `LearningModule` como entidade persistida acima de `ExerciseTrack`;
- `ExerciseType` passou a existir como taxonomia própria no banco;
- `ExerciseTrack` foi enriquecida com metadados editoriais (`goal`, `level_label`, `concept_kicker`, `milestone_*`) e relações persistidas para conceitos e pré-requisitos;
- `Exercise` passou a carregar `exercise_type`, `estimated_time_minutes`, `track_position`, `concept_summary` e `pedagogical_brief`;
- o backend expõe `Navigator` por módulos, detalhe de módulo e endpoints internos de administração do catálogo;
- o `Django admin` foi expandido para operar essa camada;
- a primeira onda de seed já materializa `5` módulos iniciais, com foco profundo em `Lógica de Programação com Python` e scaffolds para `FastAPI`, `Vue`, `Integração Full-stack` e `OCP 17`.
- o módulo `Preparatório OCP 17` já pode ser sincronizado a partir de um JSON curado externo via comando `sync_ocp17_catalog`, que substitui o scaffold inicial por trilhas reais do percurso de certificação, com conceitos e pré-requisitos persistidos.

Isso significa que a `M4` já começou de fato e deixou de depender apenas de `catalog.py` para a maior parte dos metadados editoriais relevantes.

## Reenquadramento da milestone

Esta milestone passou a ser a **próxima prioridade operacional** depois da `M2`.

O motivo é simples: antes de sofisticar ranking e gamificação, o produto precisa deixar de depender de um catálogo editorial hardcoded para ordem, tipo e metadados pedagógicos. A `M4` deixa de ser apenas “mais exercícios complexos” e passa a ser a fase em que o catálogo vira infraestrutura real de produto.

## Problema

O catálogo atual é muito bom para prova e fundamentos, mas ainda não puxa o produto para desafios mais práticos e sistêmicos.

## Objetivo

Consolidar um catálogo real, persistido e editável, e usar essa base para modelar de forma negocial as próximas famílias de trilhas, categorias e tipos de exercício.

Só depois dessa consolidação a expansão para exercícios multi-etapa e integradores passa a ter base saudável.

## Objetivos concretos desta rodada

- tirar `exercise_type`, `estimated_time_minutes` e ordem pedagógica da dependência exclusiva de `catalog.py`;
- persistir metadados editoriais/taxonômicos mínimos no domínio;
- permitir que novas trilhas sejam modeladas sem depender de deploy para cada ajuste;
- usar a modelagem das novas trilhas para definir melhor as categorias e tipologias iniciais do produto.

## Direção

Além de fundamentos, o produto deve oferecer trilhas como:

- modelagem e orientação a objetos;
- algoritmos um pouco mais ricos;
- leitura de requisito e implementação;
- mini-APIs;
- persistência e banco;
- integração frontend/backend;
- arquitetura mínima + implementação.

Mas a expansão não deve começar “jogando exercícios novos no banco”. Ela deve partir de uma pergunta negocial mais correta:

> quais famílias de prática a plataforma realmente quer sustentar, e como isso se traduz em categorias, trilhas e tipos de exercício persistidos no domínio?

## Ordem interna sugerida

1. consolidar catálogo real e persistência dos metadados hoje hardcoded;
2. modelar novas famílias de trilha com base negocial;
3. refinar categorias e `exercise_type` a partir dessa modelagem;
4. só então ampliar o catálogo com exercícios integradores mais ricos.

## Formatos de desafio possíveis

- completar feature parcial;
- corrigir solução quebrada;
- implementar a partir de um mini requisito;
- refatorar código ruim;
- integrar módulos separados;
- projeto incremental em várias etapas.

## Impacto no sistema

Essa milestone depende das anteriores porque:

- catálogo avançado sem taxonomia vira bagunça;
- ranking sem catálogo real e variedade de desafios fica raso;
- IA precisará revisar problemas mais amplos, não só saídas simples.

Também é esta milestone que passa a destravar a próxima:

- a `M3` fica mais forte quando nasce sobre categorias, trilhas e tipos de exercício já estabilizados no domínio, e não sobre taxonomia provisória.

## Critério de aceite

O produto deixa de depender de catálogo hardcoded como única fonte de verdade para progressão editorial e passa a suportar expansão de trilhas e exercícios de forma mais negocial, persistida e sustentável.

No momento, esse critério está **parcialmente atendido**: a infraestrutura persistida já existe e o módulo Python já foi semeado, mas ainda há espaço para reduzir ainda mais a função residual de `catalog.py` e aprofundar a curadoria do catálogo novo.
