# M1 - Integridade da Progressão

## Problema

Hoje o operador pode subir de nível infinitamente ao repetir submissões equivalentes. Isso destrói o valor semântico do XP e contamina qualquer ranking futuro.

## Objetivo

Fazer o XP refletir progresso real, e não repetição, sem transformar o sistema em algo opaco ou difícil de explicar.

## Pergunta que abriu esta milestone

O modelo inicial sugeria algo como `best_submission_id` + XP parcial em reexecuções melhores. A dúvida correta aqui é: isso representa bem o progresso ou cria um sistema delicado demais?

A resposta mais sólida é: **`best_submission_id` pode existir, mas não deve ser a base do sistema de progressão**.

## Aprendizados de plataformas de referência

### Codewars

O Codewars separa duas escalas:

- `Rank`, que mede proficiência;
- `Honor`, que mede atividade e contribuição.

O dado mais importante para nós é este: o rank geral sobe quando você completa um kata que **ainda não tinha resolvido antes**, e essa evolução ocorre **uma vez por kata**. Repetições não continuam inflando o rank geral. Já o `Honor` é uma superfície mais ampla de atividade e contribuição.  
Fonte: [Codewars Rewards and Progress](https://docs.codewars.com/gamification/) e [Codewars Ranks](https://docs.codewars.com/gamification/ranks/).

### HackerRank

O HackerRank trabalha com badges por trilha e pontuação por prática, mas impõe guardrails importantes. Um deles é explícito: se você desbloqueia o editorial e resolve o desafio em certos tracks, isso **não conta para o progresso**.  
Fonte: [HackerRank Scoring](https://www.hackerrank.com/scoring/score-evaluation).

### Exercism

O Exercism usa badges e trophies mais como marcos de comportamento e trilha do que como rating competitivo bruto. Um detalhe importante: alguns badges são permanentes, e os track trophies recompensam progresso específico por trilha sem necessariamente virar reputação competitiva.  
Fonte: [Exercism Track Trophies](https://forum.exercism.org/t/track-trophies-are-live/6957) e [Official Exercism Badges](https://forum.exercism.org/t/the-official-list-of-exercism-badges/3025).

### LeetCode

O LeetCode separa uma superfície competitiva baseada em rating de contest. O badge pode subir ou desaparecer conforme o rating muda. Ou seja: é uma camada diferente do simples “completei algo”.  
Fonte: [LeetCode contest badge](https://leetcode.com/discuss/post/934706/The-new-contest-badge-is-here/).

## Síntese do benchmark

O padrão mais saudável é separar pelo menos duas coisas:

- progresso persistente e anti-farm;
- atividade ou competição, que podem ter outra lógica.

Inferência a partir das fontes: as plataformas maduras tendem a evitar que o mesmo artefato resolvido infinitamente continue gerando avanço estrutural.

## Recomendação para o Logic Arena

### 1. Separar progresso persistente de dopamina operacional

O `Logic Arena` deve ter:

- `Mastery XP`: progresso persistente baseado em marcos únicos por exercício;
- `Session Feedback`: animações, heat, confete e pequenos sinais imediatos de uso;
- `Rating` futuro: camada competitiva separada, a ser tratada depois na `M3`.

### 2. Não premiar submissão; premiar mudança de estado

O XP não deve ser calculado como “ganhou mais X por executar”. Ele deve ser calculado como “você atingiu um estado pedagógico novo neste exercício”.

Exemplos de estados:

- primeira aprovação total;
- primeiro alcance de determinado threshold de testes passados;
- primeira conclusão sem hints;
- primeira conclusão em uma dificuldade nova.

### 3. Preferir marcos únicos a XP parcial contínuo

Em vez de XP parcial a cada pequena melhora, a recomendação mais segura é trabalhar com **checkpoints únicos** por exercício.

Exemplo inicial simples:

- `50%` dos testes pela primeira vez;
- `100%` dos testes pela primeira vez.

Ou, para exercícios pequenos, apenas:

- primeira aprovação total.

Isso é mais explicável, menos manipulável e menos frágil do que recalcular delta fino a cada submissão.

## Modelo de domínio recomendado

Criar um agregado explícito de progresso por usuário e exercício, algo como `UserExerciseProgress`.

Campos recomendados:

- `user`
- `exercise`
- `attempts_count`
- `last_submission_id`
- `best_passed_tests`
- `best_total_tests`
- `best_ratio`
- `first_passed_at`
- `first_pass_submission_id`
- `best_progress_submission_id`
- `awarded_milestones` ou campo equivalente
- `xp_awarded_total`

## O papel de `best_submission_id`

### Onde ele ajuda

- reabrir a tentativa que estabeleceu o melhor estado conhecido;
- facilitar auditoria e debugging;
- mostrar na UI qual submissão virou referência.

### Onde ele atrapalha

- se virar a fonte principal da regra de negócio;
- se “best” ficar ambíguo entre melhor score, melhor estilo, menor tempo ou primeira aprovação;
- se a lógica de recompensa depender demais de um único ponteiro e não de estado agregado.

### Conclusão

`best_submission_id` é útil como **referência auxiliar**, não como núcleo da progressão.

## Proposta concreta de regra inicial

### Fase 1

- `0 XP` por simples submissão;
- `XP cheio` na primeira aprovação total do exercício;
- `0 XP` para reexecução com resultado igual ou pior;
- `0 XP` para nova aprovação total do mesmo exercício, salvo futura camada de desafio especial.

### Fase 1.5, se quisermos mais nuance

Adicionar um único marco intermediário para exercícios com muitos testes:

- `XP parcial único` ao atingir pela primeira vez um threshold relevante, como `50%`;
- `XP restante` na primeira aprovação total.

Mas isso só vale a pena se a maioria dos exercícios tiver granularidade de teste suficiente para isso fazer sentido.

## Prós e contras das opções

### Opção A — XP só na primeira aprovação total

Prós:

- simples;
- fácil de explicar;
- praticamente elimina farm;
- muito alinhada ao padrão “first completion counts”.

Contras:

- pode parecer seca para exercícios mais longos;
- não recompensa melhora parcial.

### Opção B — XP por marcos únicos

Prós:

- mantém integridade;
- recompensa progresso intermediário real;
- continua explicável.

Contras:

- exige definição cuidadosa dos marcos;
- pode ficar artificial em exercícios muito pequenos.

### Opção C — XP parcial contínuo por delta

Prós:

- parece sofisticada;
- acompanha melhora gradual.

Contras:

- é mais difícil de explicar;
- mais suscetível a edge cases;
- mais delicada de manter;
- mais fácil de gerar comportamento de farm “otimizado”.

## Recomendação final desta nota

Para o `Logic Arena`, a recomendação mais segura é:

1. começar com `XP por marcos únicos`, com regra mínima;
2. tratar `best_progress_submission_id` e `first_pass_submission_id` apenas como referências de auditoria/UI;
3. não usar delta contínuo como motor principal da progressão;
4. deixar a camada competitiva para a `M3`.

## Mudanças de API

- a submissão deve devolver:
  - se houve marco novo;
  - qual marco foi ganho;
  - quanto XP foi concedido;
  - qual é o novo estado de progresso do exercício.

## Mudanças de frontend

- parar de calcular XP apenas localmente;
- exibir com clareza quando a rodada valeu XP e por quê;
- destacar “primeira aprovação” ou “novo marco”;
- manter animações locais sem confundir isso com progressão real.

## Subtarefas naturais

1. modelar progresso persistido por usuário e exercício;
2. definir schema de marcos recompensáveis;
3. calcular recompensa no backend por mudança de estado;
4. adaptar a arena para consumir esse novo payload;
5. migrar o XP local legado com fallback controlado.

## Critério de aceite

Um usuário não consegue subir de nível repetindo infinitamente a mesma solução aprovada sem qualquer melhora, e a regra de recompensa continua simples o suficiente para ser explicada em uma frase na UI.

## Status da implementação

### Fatia já implementada

- `ArenaUser.xp_total` no backend;
- agregado `UserExerciseProgress` por `usuário + exercício`;
- milestone única `passed_once`;
- recompensa persistida por submissão com `xp_awarded` e `unlocked_progress_rewards`;
- payload de progressão devolvido na submissão;
- frontend sem persistência local de XP/nível/progresso como fonte de verdade.
- distinção visual melhor entre `passou`, `ganhou XP` e `subiu de nível` na arena.

### Ainda não entrou

- thresholds intermediários como `halfway_once`;
- achievements/trophies transversais;
- ranking competitivo;
- trilhas e mastery por categoria.

## Próxima leitura

- [[M1 - Especificação Técnica da Progressão]]
