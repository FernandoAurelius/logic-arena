# Progressão, History e Gamificação

## Objetivo do módulo

Este contexto responde à pergunta: como o produto transforma prática repetida em sensação de progresso e memória útil?

## Arquivos principais

- `frontend/src/views/ArenaView.vue`
- `backend/arena/models.py`
- `backend/arena/api.py`

## O que existe hoje

- XP local por operador;
- nível calculado a partir do XP;
- confete ao concluir exercício com sucesso;
- indicador de `forge heat` durante digitação;
- history colapsável;
- restauração de submissão com código, console e chat.

Trecho atual:

```ts
function awardXp(amount: number) {
  if (!session.currentUser.value) return
  const previousLevel = level.value
  xp.value += amount
  level.value = Math.max(1, Math.floor(xp.value / 100) + 1)
  persistProgress()
  if (level.value > previousLevel) {
    triggerLevelUp()
    triggerConfetti()
  }
}
```

## Problema atual

O desenho atual recompensa submissão, não progresso real. Isso permite farmar XP repetindo execuções sem ganho pedagógico.

Esse é o ponto mais crítico da gamificação hoje. Sem corrigi-lo, toda a camada de ranking futura nasce contaminada.

## History como memória, não só log

O history começou como uma lista de submissões, mas já evoluiu para algo mais valioso:

- reabre a sessão anterior;
- restaura o código submetido;
- reapresenta o console;
- traz o feedback automático;
- traz o histórico do chat com IA.

Essa decisão é forte porque desloca o valor do app: ele não é só um lugar para “tentar de novo”, mas também um lugar para revisar o que já aconteceu.

## Tese para a evolução

O sistema precisa separar três conceitos:

- `XP`: progressão local e motivacional;
- `rating`: sinal competitivo;
- `mastery`: domínio real por categoria/trilha.

Hoje só o primeiro existe, e ainda de forma frágil.

## Por onde continuar

- [[../04_Milestones/M1 - Integridade da Progressão]]
- [[../04_Milestones/M3 - Ranking e Gamificação Útil]]
