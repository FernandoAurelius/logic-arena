# M1 - Especificação Técnica da Progressão

## Objetivo desta nota

Transformar a decisão conceitual da `M1` em uma proposta técnica implementável sem ambiguidade.

Hoje o sistema calcula XP apenas no frontend, de forma local:

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

E a submissão chama isso de forma direta:

```ts
awardXp(submission.status === 'passed' ? 35 : 10)
```

Esse é o ponto que precisa morrer primeiro.

## Princípio técnico central

O backend passa a ser a fonte de verdade da progressão.

O frontend pode continuar:

- animando level up;
- disparando confete;
- mostrando barras;

mas não deve mais decidir sozinho quando houve ganho estrutural de XP.

## Modelo de domínio proposto

### Nova entidade

Criar um modelo persistido por usuário e exercício:

```python
class UserExerciseProgress(TimestampedModel):
    user = models.ForeignKey(ArenaUser, on_delete=models.CASCADE, related_name='exercise_progress')
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, related_name='user_progress')
    attempts_count = models.PositiveIntegerField(default=0)
    last_submission = models.ForeignKey(
        Submission,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )
    best_progress_submission = models.ForeignKey(
        Submission,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )
    first_pass_submission = models.ForeignKey(
        Submission,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )
    best_passed_tests = models.PositiveIntegerField(default=0)
    best_total_tests = models.PositiveIntegerField(default=0)
    best_ratio = models.DecimalField(max_digits=5, decimal_places=4, default=0)
    first_passed_at = models.DateTimeField(null=True, blank=True)
    awarded_progress_markers = models.JSONField(default=list, blank=True)
    xp_awarded_total = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('user', 'exercise')
```

## Por que esse shape

### `attempts_count`

Permite medir persistência sem depender de consultas agregadas posteriores.

### `last_submission`

Ajuda a reabrir e auditar o estado mais recente sem ambiguidade.

### `best_progress_submission`

Não representa “melhor código” em sentido amplo. Representa a submissão que estabeleceu o melhor estado de progresso conhecido.

### `first_pass_submission`

É útil porque “primeira aprovação” tem semântica própria e futura utilidade para badges, ranking e UI.

### `best_passed_tests`, `best_total_tests`, `best_ratio`

São os dados que sustentam a regra de progressão sem depender apenas de ponteiros para submissão.

### `awarded_progress_markers`

Permite registrar **apenas marcos de progressão estrutural daquele exercício** já concedidos.

Esse ponto precisa ser tratado com bastante disciplina: progresso local do exercício não deve ser confundido com sistema mais amplo de conquistas, trophies, badges ou ranking.

Exemplos iniciais seguros:

- `passed_once`
- `halfway_once`

Exemplos que **não** deveriam entrar aqui por enquanto:

- `passed_without_hints_once`
- `completed_under_2_minutes`
- `solved_three_exercises_in_a_row`

Esses últimos pertencem mais naturalmente a uma camada futura de `achievements/trophies`, porque dependem de contexto transversal, tempo, comportamento, categoria ou sessão.

## Separação correta entre progresso e conquistas

### 1. Progress markers

São marcos estritamente ligados ao par `usuário + exercício`.

Servem para:

- conceder XP estrutural;
- impedir recompensa duplicada;
- explicar o estado de domínio naquele exercício.

Exemplos:

- primeira aprovação total;
- primeiro threshold de testes atingido.

### 2. Achievements / Trophies

São conquistas mais amplas, de produto e gamificação.

Podem depender de:

- categoria;
- assunto;
- streak;
- tempo de execução;
- hints usados;
- sequência de vitórias;
- faixa de dificuldade;
- diversidade de trilhas;
- consistência semanal.

Essas conquistas devem ser tratadas numa camada própria, provavelmente dentro da `M3`, e não embutidas no primeiro desenho de progressão.

### Conclusão prática

Na `M1`, o backend deve persistir apenas `progress markers`, não um sistema geral de conquistas.

## Regra inicial recomendada

### Versão 1.0

A primeira implementação deve ser propositalmente conservadora:

- `0 XP` por submissão simples;
- `0 XP` por falha;
- `35 XP` na primeira aprovação total de um exercício;
- `0 XP` em aprovações posteriores do mesmo exercício.

### Por que começar assim

- mata o problema do farm imediatamente;
- é muito fácil de explicar;
- reduz a chance de bug de negócio;
- não impede evoluir depois.

## Regra 1.1 opcional

Se quisermos dar nuance depois, podemos adicionar um milestone intermediário **único** para exercícios com vários testes:

- `15 XP` ao atingir `>= 50%` dos testes pela primeira vez;
- `20 XP` na primeira aprovação total;
- total continua `35 XP`.

Mas essa regra só deve entrar se o catálogo realmente tiver granularidade suficiente para isso fazer sentido. Para o momento, a minha recomendação continua sendo **não implementar isso na primeira rodada**.

## Onde o XP do usuário deve viver

Hoje ele só existe no frontend. A proposta é mover para o backend.

### Opção recomendada

Adicionar no próprio `ArenaUser`:

```python
class ArenaUser(TimestampedModel):
    nickname = models.CharField(max_length=40, unique=True)
    password_hash = models.CharField(max_length=255)
    xp_total = models.PositiveIntegerField(default=0)
```

O nível continua derivado:

```text
level = floor(xp_total / 100) + 1
```

### Por que não guardar level também

Porque `level` é derivável e, neste estágio, não precisa ser persistido separadamente.

## Contrato de API proposto

### Novo schema de progresso

```python
class ProgressRewardSchema(Schema):
    milestone_key: str
    label: str
    xp_awarded: int


class ExerciseProgressSchema(Schema):
    attempts_count: int
    best_passed_tests: int
    best_total_tests: int
    best_ratio: float
    xp_awarded_total: int
    first_passed_at: datetime | None
    awarded_progress_markers: list[str]


class UserProgressSummarySchema(Schema):
    xp_total: int
    level: int
    xp_into_level: int
    xp_to_next_level: int
```

### Evolução do `SubmissionSchema`

Adicionar:

```python
class SubmissionSchema(Schema):
    ...
    xp_awarded: int
    unlocked_progress_rewards: list[ProgressRewardSchema]
    exercise_progress: ExerciseProgressSchema
    user_progress: UserProgressSummarySchema
```

### Semântica do retorno

- `xp_awarded`: quanto esta submissão concedeu;
- `unlocked_progress_rewards`: quais marcos de progressão foram desbloqueados;
- `exercise_progress`: estado persistido daquele exercício para o usuário;
- `user_progress`: progresso agregado do operador.

## Mudanças mínimas de endpoint

### `POST /api/submissions/exercises/{slug}/submit`

Passa a:

- avaliar a submissão;
- atualizar `UserExerciseProgress`;
- atualizar `ArenaUser.xp_total`;
- devolver o novo estado de progressão.

### `GET /api/auth/me`

Pode passar a incluir `xp_total` e `level`, para hidratar a arena logo no boot.

## Fluxo interno proposto no backend

1. criar e persistir `Submission`;
2. buscar ou criar `UserExerciseProgress`;
3. incrementar `attempts_count`;
4. atualizar `last_submission`;
5. comparar score atual com o melhor já conhecido;
6. identificar se houve desbloqueio de milestone;
7. calcular `xp_awarded`;
8. atualizar `xp_total` do usuário;
9. devolver o payload completo.

## Regras de integridade

### Regra 1

Uma mesma `milestone_key` não pode render XP duas vezes para o mesmo `user + exercise`.

### Regra 2

Se a submissão não melhora o estado e não desbloqueia marco, `xp_awarded = 0`.

### Regra 3

`best_progress_submission` só muda quando o estado de progresso melhora de fato.

### Regra 4

`first_pass_submission` e `first_passed_at` só são definidos na primeira aprovação total.

## Impacto no frontend

### Remover

- cálculo local soberano de XP;
- `awardXp(submission.status === 'passed' ? 35 : 10)`.
- qualquer persistência de progresso em `localStorage`.

### Manter

- animação de level up;
- confete;
- barra de progresso;
- nenhuma fonte paralela de verdade para XP, level ou marcos.

### Adicionar

- banner curto de recompensa:
  - `Primeira aprovação: +35 XP`
  - ou `Sem ganho de XP nesta rodada`
- distinção visual entre:
  - passou;
  - ganhou XP;
  - subiu de nível.

Esses três eventos não são a mesma coisa.

## Estratégia de migração

### Etapa 1

Adicionar o modelo novo e os campos em `ArenaUser`.

### Etapa 2

Passar a escrever o progresso novo nas submissões futuras.

### Etapa 3

No frontend, consumir exclusivamente o novo payload do backend.

### Etapa 4

Remover totalmente:

- `progressStorageKey`
- `hydrateProgress`
- `persistProgress`
- qualquer reaproveitamento de `localStorage` para XP/nível

O frontend pode continuar persistindo apenas preferências realmente locais, como tema ou colapso visual de painéis, mas nunca progresso do produto.

## Ordem de implementação recomendada

### Backend

1. migration para `ArenaUser.xp_total`
2. migration para `UserExerciseProgress`
3. schemas novos de progressão
4. service de progressão
5. integração no endpoint de submissão
6. endpoint `me` enriquecido com progresso agregado

### Frontend

1. atualizar types/client
2. ler `user_progress` no boot da arena
3. remover persistência local de XP/nível
4. implementar banners de recompensa
5. manter animações com base no delta recebido

## Riscos e mitigação

### Risco

Misturar “passou” com “ganhou XP”.

### Mitigação

UI explícita separando:

- status da submissão;
- recompensa da rodada;
- mudança de nível.

### Risco

Misturar progress markers com trophies futuros e criar um modelo confuso desde a base.

### Mitigação

Limitar a `M1` a progressão por exercício e empurrar achievements transversais para uma camada posterior.

### Risco

Complexidade demais cedo demais.

### Mitigação

Implementar primeiro a versão conservadora: XP só na primeira aprovação total.

## Recomendação final

Se a meta é fazer a `M1` com segurança, a primeira rodada deve implementar apenas:

- `UserExerciseProgress`
- `ArenaUser.xp_total`
- milestone única `passed_once`
- nenhuma persistência local de progresso no frontend
- novo payload de progressão na submissão
- remoção do XP calculado localmente como fonte de verdade

Isso já resolve o problema real sem introduzir engenharia excessiva.
