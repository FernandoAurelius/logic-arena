# Arena Frontend e Experiência

## Objetivo do módulo

Esta camada organiza a experiência do usuário. Ela não é apenas “a UI”: ela determina o quanto a prática parece fluida, clara e próxima de uma situação real de prova.

## Arquivos principais

- `frontend/src/views/LandingView.vue`
- `frontend/src/views/TutorialView.vue`
- `frontend/src/views/ArenaView.vue`
- `frontend/src/components/editor/MonacoEditor.vue`
- `frontend/src/lib/session.ts`
- `frontend/src/lib/theme.ts`

## Superfícies atuais

### Landing

A landing pública apresenta a proposta do produto e leva o usuário para login ou tutorial.

### Tutorial

A página de ajuda introduz os componentes principais da arena de forma guiada.

### Arena autenticada

É a estação de prática propriamente dita, com:

- topbar do produto;
- sidebar com operator, módulos e history;
- specification do desafio;
- editor;
- console;
- hints;
- feedback;
- drawer de revisão com IA.

## Código que mostra a centralidade da arena

Em `ArenaView.vue`, praticamente todo o estado do produto converge:

```ts
const activeExercise = ref<ExerciseDetail | null>(null)
const submissions = ref<SubmissionSummary[]>([])
const code = ref('')
const latestSubmission = ref<Submission | null>(null)
const chatOpen = ref(false)
const historyOpen = ref(false)
const hintsOpen = ref(false)
```

Isso revela algo importante: a arena não é uma tela qualquer, e sim o ponto de orquestração do produto inteiro.

## Leitura didática

O frontend já passou por algumas iterações relevantes:

- saiu de um protótipo em React/Vite;
- ganhou uma shell mais fiel ao design brutalista/técnico;
- separou landing e arena autenticada;
- recolocou o editor como protagonista com `Monaco`;
- transformou a revisão com IA em painel lateral colapsável.

Essas mudanças indicam uma direção correta: o produto melhora quando trata a arena como ferramenta de foco, não como dashboard.

## Tensões abertas

- a navegação do catálogo ainda é plana demais para crescer;
- parte da progressão ainda vive localmente no frontend;
- a composição ideal entre specification, editor, console e revisão ainda pode evoluir.

## Por onde continuar

- [[Progressão, History e Gamificação]]
- [[../04_Milestones/M2 - Taxonomia e Navegação Canônica]]
