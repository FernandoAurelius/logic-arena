# M3 - Ranking e Gamificação Útil

## Problema

A gamificação atual já dá prazer de uso, mas ainda não possui um sistema robusto que justifique comparação, status e progressão pública.

## Objetivo

Criar um modelo de dopamina útil: competitivo o suficiente para engajar, pedagógico o suficiente para não premiar comportamento vazio.

## Princípios

- `XP` não é ranking;
- ranking não pode premiar spam;
- domínio por categoria é mais útil do que score bruto;
- streak e consistência devem valer, mas não dominar tudo.
- achievements e trophies não devem contaminar a regra básica de progressão da `M1`.

## Modelo sugerido

Separar três camadas:

- `XP`: sensação de progresso local
- `rating`: posição competitiva
- `mastery`: domínio por trilha e assunto

E adicionar uma quarta camada, mas apenas quando o produto estiver pronto para isso:

- `achievements/trophies`: conquistas temáticas, comportamentais e de consistência

## Sinais candidatos para o rating

- primeira aprovação;
- dificuldade do exercício;
- taxa de sucesso;
- hints usados;
- número de tentativas;
- tempo até primeira aprovação;
- variedade de assuntos dominados.

## UX esperada

- tela de perfil/ranking simples;
- badges por conquista real;
- feedback de subida de rank;
- metas curtas e streaks significativas.

## Roadmap sugerido para achievements/trophies

Essa camada deve nascer depois da integridade da progressão e da taxonomia do catálogo. O motivo é simples: as melhores conquistas dependem de tema, dificuldade, tempo, sequência e categoria.

### Famílias de conquistas candidatas

#### 1. Conquistas de domínio

- fechar uma trilha inteira;
- fechar todos os exercícios de um assunto;
- primeira vitória em uma nova faixa de dificuldade.

#### 2. Conquistas de consistência

- streak semanal;
- X dias seguidos praticando;
- X exercícios concluídos na mesma semana.

#### 3. Conquistas de eficiência

- resolver sem hints;
- resolver abaixo de um tempo-alvo;
- resolver com poucas submissões.

#### 4. Conquistas de amplitude

- concluir exercícios em múltiplas categorias;
- migrar de fundamentos para integradores;
- completar desafios em stacks diferentes.

### Regra de design

Essas conquistas devem:

- ser explicáveis;
- reforçar comportamento útil;
- nunca substituir o valor da progressão estrutural;
- nunca permitir farm vazio.

## Critério de aceite

Dois usuários que spamam execuções repetidas não sobem no ranking como se estivessem realmente evoluindo.
