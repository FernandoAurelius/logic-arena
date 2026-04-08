<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import type { infer as ZodInfer } from 'zod'

import { schemas } from './lib/api/generated'
import { authApi, exercisesApi, submissionsApi } from './lib/api/client'

type User = ZodInfer<typeof schemas.UserSchema>
type LoginResponse = ZodInfer<typeof schemas.LoginResponseSchema>
type ExerciseSummary = ZodInfer<typeof schemas.ExerciseSummarySchema>
type ExerciseDetail = ZodInfer<typeof schemas.ExerciseDetailSchema>
type Submission = ZodInfer<typeof schemas.SubmissionSchema>
type SubmissionSummary = ZodInfer<typeof schemas.SubmissionSummarySchema>

const STORAGE_KEY = 'logic-arena-session'
const nickname = ref('')
const password = ref('')
const token = ref('')
const currentUser = ref<User | null>(null)
const exercises = ref<ExerciseSummary[]>([])
const activeExercise = ref<ExerciseDetail | null>(null)
const submissions = ref<SubmissionSummary[]>([])
const code = ref('')
const latestSubmission = ref<Submission | null>(null)
const isBusy = ref(false)
const loginBusy = ref(false)
const errorMessage = ref('')
const loginMessage = ref('')

const isAuthenticated = computed(() => Boolean(token.value && currentUser.value))
const activeProgress = computed(() => {
  if (!latestSubmission.value || latestSubmission.value.total_tests === 0) return 0
  return Math.round((latestSubmission.value.passed_tests / latestSubmission.value.total_tests) * 100)
})
const activeIndex = computed(() => {
  if (!activeExercise.value) return 0
  return exercises.value.findIndex((exercise) => exercise.slug === activeExercise.value?.slug) + 1
})
const codeLines = computed(() => {
  const total = Math.max(code.value.split('\n').length, 12)
  return Array.from({ length: total }, (_, index) => String(index + 1).padStart(2, '0'))
})
const consoleLines = computed(() => {
  if (!latestSubmission.value?.console_output) return ['[INIT] Aguardando execução do módulo atual...']
  return latestSubmission.value.console_output.split('\n').filter(Boolean)
})

function authHeader() {
  return token.value ? `Bearer ${token.value}` : null
}

function persistSession(payload: { token: string; user: User }) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(payload))
}

function clearSession() {
  localStorage.removeItem(STORAGE_KEY)
  token.value = ''
  currentUser.value = null
  submissions.value = []
  latestSubmission.value = null
}

async function bootstrap() {
  errorMessage.value = ''

  try {
    exercises.value = await exercisesApi.get('/api/exercises/')
    if (!activeExercise.value && exercises.value.length > 0) {
      await selectExercise(exercises.value[0].slug)
    }
  } catch (error) {
    errorMessage.value = 'Não foi possível carregar os exercícios da API.'
    console.error(error)
  }

  const savedSession = localStorage.getItem(STORAGE_KEY)
  if (!savedSession) return

  try {
    const parsed = JSON.parse(savedSession) as { token: string; user: User }
    token.value = parsed.token
    currentUser.value = parsed.user
    nickname.value = parsed.user.nickname
    await hydrateSession()
  } catch (error) {
    clearSession()
    console.error(error)
  }
}

async function hydrateSession() {
  if (!token.value) return

  try {
    const me = await authApi.get('/api/auth/me', {
      headers: { authorization: authHeader() ?? undefined },
    })
    currentUser.value = me
    persistSession({ token: token.value, user: me })
    submissions.value = await submissionsApi.get('/api/submissions/me', {
      headers: { authorization: authHeader() ?? undefined },
    })
  } catch (error) {
    console.error(error)
    clearSession()
  }
}

async function login() {
  loginBusy.value = true
  loginMessage.value = ''
  errorMessage.value = ''

  try {
    const response = (await authApi.post('/api/auth/login', {
      nickname: nickname.value.trim(),
      password: password.value,
    })) as LoginResponse
    token.value = response.token
    currentUser.value = response.user
    persistSession({ token: response.token, user: response.user })
    loginMessage.value = response.created
      ? 'Usuário criado automaticamente e sessão iniciada.'
      : 'Sessão iniciada com sucesso.'
    await hydrateSession()
  } catch (error) {
    console.error(error)
    errorMessage.value = 'Não foi possível autenticar com esse nickname e senha.'
  } finally {
    loginBusy.value = false
  }
}

async function selectExercise(slug: string) {
  isBusy.value = true
  errorMessage.value = ''

  try {
    const exercise = await exercisesApi.get('/api/exercises/:slug', {
      params: { slug },
    })
    activeExercise.value = exercise
    code.value = exercise.starter_code
    latestSubmission.value = null
  } catch (error) {
    console.error(error)
    errorMessage.value = 'Falha ao carregar os detalhes do exercício.'
  } finally {
    isBusy.value = false
  }
}

async function submitSolution() {
  if (!activeExercise.value || !token.value) {
    errorMessage.value = 'Faça login antes de submeter uma solução.'
    return
  }

  isBusy.value = true
  errorMessage.value = ''

  try {
    const exercise = activeExercise.value
    if (!exercise) return

    latestSubmission.value = await submissionsApi.post(
      '/api/submissions/exercises/:slug/submit',
      { source_code: code.value },
      { params: { slug: exercise.slug }, headers: { authorization: authHeader() ?? undefined } },
    )
    submissions.value = await submissionsApi.get('/api/submissions/me', {
      headers: { authorization: authHeader() ?? undefined },
    })
  } catch (error) {
    console.error(error)
    errorMessage.value = 'Não foi possível processar a submissão.'
  } finally {
    isBusy.value = false
  }
}

watch(
  () => activeExercise.value?.slug,
  () => {
    if (activeExercise.value && !code.value) {
      code.value = activeExercise.value.starter_code
    }
  },
)

onMounted(() => {
  void bootstrap()
})
</script>

<template>
  <div class="terminal-shell">
    <header class="topbar">
      <div class="topbar-left">
        <span class="brand-wordmark">IGNITION_OS</span>
        <nav class="topnav">
          <a class="active" href="#">COMPILER</a>
          <a href="#">REPOSITORY</a>
          <a href="#">DEBUGGER</a>
        </nav>
      </div>
      <div class="topbar-right">
        <div class="level-box">
          <strong>LEVEL 42</strong>
          <span>{{ currentUser?.nickname ?? 'guest_operator' }}</span>
        </div>
        <div class="icon-row">
          <span class="material-symbols-outlined">terminal</span>
          <span class="material-symbols-outlined">settings</span>
          <span class="material-symbols-outlined">account_circle</span>
        </div>
      </div>
    </header>

    <div class="terminal-body">
      <aside class="sidenav">
        <div class="operator-card">
          <div class="operator-icon">
            <span class="material-symbols-outlined">memory</span>
          </div>
          <div>
            <p class="eyebrow">Operator</p>
            <strong>{{ currentUser?.nickname ?? 'OPERATOR_01' }}</strong>
            <small>STATUS: {{ isAuthenticated ? 'ROOT_ACCESS' : 'LOCKED' }}</small>
          </div>
        </div>

        <section class="auth-panel">
          <p class="eyebrow">Access Node</p>
          <label>
            <span>Nickname</span>
            <input v-model="nickname" placeholder="miguel" />
          </label>
          <label>
            <span>Senha</span>
            <input v-model="password" type="password" placeholder="••••••••" />
          </label>
          <div class="auth-actions">
            <button class="primary-btn" :disabled="loginBusy || !nickname || !password" @click="login">
              {{ loginBusy ? 'SYNCING...' : 'LOGIN' }}
            </button>
            <button class="ghost-btn" :disabled="!isAuthenticated" @click="clearSession">LOGOUT</button>
          </div>
          <p v-if="loginMessage" class="notice success">{{ loginMessage }}</p>
        </section>

        <nav class="module-nav">
          <p class="eyebrow">Core Modules</p>
          <button
            v-for="exercise in exercises"
            :key="exercise.slug"
            class="module-link"
            :class="{ active: activeExercise?.slug === exercise.slug }"
            @click="selectExercise(exercise.slug)"
          >
            <span class="material-symbols-outlined">account_tree</span>
            <div>
              <strong>{{ exercise.title }}</strong>
              <small>{{ exercise.difficulty }} · {{ exercise.language }}</small>
            </div>
          </button>
        </nav>

        <section class="history-panel">
          <p class="eyebrow">History</p>
          <ul>
            <li v-for="submission in submissions.slice(0, 5)" :key="submission.id">
              <strong>{{ submission.exercise_title }}</strong>
              <span>{{ submission.passed_tests }}/{{ submission.total_tests }} · {{ submission.status }}</span>
            </li>
            <li v-if="submissions.length === 0" class="dimmed">Nenhuma execução persistida.</li>
          </ul>
        </section>
      </aside>

      <main class="workspace">
        <div class="blueprint-grid"></div>

        <section class="workspace-header">
          <div>
            <div class="breadcrumb">
              <span>Programming Logic</span>
              <span class="material-symbols-outlined tiny">chevron_right</span>
              <span class="active">{{ activeExercise?.difficulty ?? 'Challenge' }}</span>
            </div>
            <h1>Challenge: {{ activeExercise?.title ?? 'Awaiting Exercise' }}</h1>
            <p class="workspace-copy">
              {{ activeExercise?.statement ?? 'Selecione um exercício no rail lateral para começar a estação prática.' }}
            </p>
          </div>
          <div class="status-box">
            <span class="status-dot"></span>
            <span>Terminal Status: {{ isBusy ? 'Running' : 'Active' }}</span>
          </div>
        </section>

        <p v-if="errorMessage" class="notice error">{{ errorMessage }}</p>

        <section v-if="activeExercise" class="two-column">
          <div class="left-column">
            <article class="spec-card">
              <h3>Technical Specification</h3>
              <p>{{ activeExercise.statement }}</p>
              <div class="formula-box">
                <p>// BANKA NOTE</p>
                <strong>{{ activeExercise.professor_note || 'Sem anotação adicional.' }}</strong>
              </div>
              <div class="io-card">
                <p class="section-label">Input Examples</p>
                <ul class="input-list">
                  <li><code>{{ activeExercise.sample_input }}</code></li>
                  <li><code>{{ activeExercise.sample_output }}</code></li>
                </ul>
              </div>
            </article>

            <article class="metrics-card">
              <h4>Efficiency Metrics</h4>
              <div class="metric-line">
                <div>
                  <strong>{{ activeProgress }}%</strong>
                  <span>Current mastery for this module</span>
                </div>
                <div class="progress-track">
                  <div class="progress-fill" :style="{ width: `${activeProgress}%` }"></div>
                </div>
              </div>
            </article>
          </div>

          <div class="right-column">
            <div class="editor-header">
              <div class="window-dots">
                <span class="dot red"></span>
                <span class="dot amber"></span>
                <span class="dot gray"></span>
              </div>
              <span class="file-name">{{ activeExercise.slug }}.py</span>
              <span class="material-symbols-outlined">more_horiz</span>
            </div>

            <div class="editor-canvas">
              <div class="line-gutter">
                <span v-for="line in codeLines" :key="line">{{ line }}</span>
              </div>
              <textarea v-model="code" class="code-editor" spellcheck="false" />
            </div>

            <div class="console-card">
              <div class="console-header">
                <span class="material-symbols-outlined">terminal</span>
                <strong>Console Output</strong>
              </div>
              <div class="console-body">
                <div v-for="(line, index) in consoleLines" :key="`${index}-${line}`" class="console-line">
                  <span class="console-time">{{ String(index).padStart(2, '0') }}:42</span>
                  <span :class="line.includes('PASSOU') ? 'tag pass' : line.includes('FALHOU') ? 'tag fail' : 'tag exec'">
                    {{ line.includes('PASSOU') ? '[PASS]' : line.includes('FALHOU') ? '[FAIL]' : '[EXEC]' }}
                  </span>
                  <span>{{ line }}</span>
                </div>
              </div>
              <button class="execute-btn" :disabled="isBusy || !isAuthenticated" @click="submitSolution">
                <span class="material-symbols-outlined">play_arrow</span>
                <span>{{ isBusy ? 'Executing...' : 'Execute Module' }}</span>
              </button>
            </div>
          </div>
        </section>

        <section class="mastery-strip">
          <div class="mastery-copy">
            <h5>Mastery Progression</h5>
            <div class="mastery-meter">
              <div class="mastery-meter-fill" :style="{ width: `${activeProgress}%` }"></div>
            </div>
          </div>
          <div class="badge-grid">
            <div class="badge-card active">
              <span class="material-symbols-outlined">psychology</span>
              <span>Logic Sage</span>
            </div>
            <div class="badge-card muted">
              <span class="material-symbols-outlined">memory</span>
              <span>Bit Master</span>
            </div>
            <div class="badge-card active">
              <span class="material-symbols-outlined">hub</span>
              <span>Tree Walker</span>
            </div>
          </div>
        </section>

        <section v-if="latestSubmission" class="feedback-band">
          <div class="feedback-metric">
            <span class="eyebrow">Submission</span>
            <strong>{{ latestSubmission.passed_tests }}/{{ latestSubmission.total_tests }}</strong>
          </div>
          <div class="feedback-metric">
            <span class="eyebrow">Status</span>
            <strong>{{ latestSubmission.status }}</strong>
          </div>
          <div class="feedback-text">
            <span class="eyebrow">System Feedback</span>
            <p>{{ latestSubmission.feedback }}</p>
          </div>
          <div class="feedback-metric">
            <span class="eyebrow">Quest</span>
            <strong>{{ activeIndex }}/{{ exercises.length || 1 }}</strong>
          </div>
        </section>
      </main>
    </div>
  </div>
</template>
