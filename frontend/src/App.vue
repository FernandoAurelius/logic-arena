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
  <div class="app-shell">
    <aside class="sidebar">
      <div class="brand-block">
        <p class="eyebrow">Logic Arena MVP</p>
        <h1>Treino interno com persistência real</h1>
        <p class="muted">
          Base em Vue 3 + TypeScript consumindo a API do Django Ninja com contrato OpenAPI tipado.
        </p>
      </div>

      <section class="panel">
        <div class="panel-head">
          <p class="eyebrow">Autenticação mínima</p>
          <h2>Nickname + senha</h2>
        </div>

        <div class="field-stack">
          <label>
            <span>Nickname</span>
            <input v-model="nickname" placeholder="ex.: miguel" />
          </label>
          <label>
            <span>Senha</span>
            <input v-model="password" type="password" placeholder="senha simples" />
          </label>
        </div>

        <div class="button-row">
          <button class="primary" :disabled="loginBusy || !nickname || !password" @click="login">
            {{ loginBusy ? 'Entrando...' : 'Entrar' }}
          </button>
          <button class="ghost" :disabled="!isAuthenticated" @click="clearSession">
            Sair
          </button>
        </div>

        <p v-if="currentUser" class="status-line">
          Sessão ativa como <strong>{{ currentUser.nickname }}</strong>
        </p>
        <p v-if="loginMessage" class="success-line">{{ loginMessage }}</p>
      </section>

      <section class="panel">
        <div class="panel-head">
          <p class="eyebrow">Exercícios</p>
          <h2>Banco persistido</h2>
        </div>

        <div class="exercise-list">
          <button
            v-for="exercise in exercises"
            :key="exercise.slug"
            class="exercise-item"
            :class="{ active: activeExercise?.slug === exercise.slug }"
            @click="selectExercise(exercise.slug)"
          >
            <strong>{{ exercise.title }}</strong>
            <span>{{ exercise.difficulty }} · {{ exercise.language }}</span>
          </button>
        </div>
      </section>

      <section class="panel">
        <div class="panel-head">
          <p class="eyebrow">Histórico</p>
          <h2>Submissões recentes</h2>
        </div>

        <ul class="submission-list">
          <li v-for="submission in submissions.slice(0, 6)" :key="submission.id">
            <strong>{{ submission.exercise_title }}</strong>
            <span>{{ submission.passed_tests }}/{{ submission.total_tests }} · {{ submission.status }}</span>
          </li>
          <li v-if="submissions.length === 0" class="muted">Nenhuma submissão salva ainda.</li>
        </ul>
      </section>
    </aside>

    <main class="content">
      <div class="hero">
        <div>
          <p class="eyebrow">Contrato tipado</p>
          <h2>{{ activeExercise?.title ?? 'Selecione um exercício' }}</h2>
          <p class="muted">
            {{ activeExercise?.statement ?? 'O exercício selecionado aparecerá aqui com starter code e casos visíveis.' }}
          </p>
        </div>
        <div class="hero-chip">
          <span>API</span>
          <strong>Django Ninja + OpenAPI</strong>
        </div>
      </div>

      <p v-if="errorMessage" class="error-banner">{{ errorMessage }}</p>

      <section v-if="activeExercise" class="workspace-grid">
        <article class="panel">
          <div class="panel-head">
            <p class="eyebrow">Leitura da banca</p>
            <h2>{{ activeExercise.professor_note || 'Sem nota do professor cadastrada.' }}</h2>
          </div>

          <div class="io-grid">
            <div class="io-card">
              <h3>Exemplo de entrada</h3>
              <pre>{{ activeExercise.sample_input }}</pre>
            </div>
            <div class="io-card">
              <h3>Saída esperada</h3>
              <pre>{{ activeExercise.sample_output }}</pre>
            </div>
          </div>

          <div class="io-card">
            <h3>Casos visíveis</h3>
            <ul class="visible-tests">
              <li v-for="testCase in activeExercise.test_cases" :key="testCase.id">
                <strong>Entrada:</strong> {{ JSON.stringify(testCase.input_data) }}
                <br />
                <strong>Esperado:</strong> {{ testCase.expected_output }}
              </li>
            </ul>
          </div>
        </article>

        <article class="panel editor-panel">
          <div class="panel-head">
            <p class="eyebrow">Submissão</p>
            <h2>Editor da solução</h2>
          </div>

          <textarea v-model="code" spellcheck="false" />

          <div class="button-row">
            <button class="ghost" @click="code = activeExercise.starter_code">Resetar código</button>
            <button class="primary" :disabled="isBusy || !isAuthenticated" @click="submitSolution">
              {{ isBusy ? 'Executando...' : 'Submeter solução' }}
            </button>
          </div>
        </article>
      </section>

      <section v-if="latestSubmission" class="panel results-panel">
        <div class="panel-head">
          <p class="eyebrow">Resultado</p>
          <h2>{{ latestSubmission.status === 'passed' ? 'Passou' : 'Ainda não passou' }}</h2>
        </div>

        <div class="result-summary">
          <div class="metric-card">
            <span>Testes</span>
            <strong>{{ latestSubmission.passed_tests }}/{{ latestSubmission.total_tests }}</strong>
          </div>
          <div class="metric-card">
            <span>Status</span>
            <strong>{{ latestSubmission.status }}</strong>
          </div>
        </div>

        <div class="feedback-box">
          <h3>Feedback básico</h3>
          <p>{{ latestSubmission.feedback }}</p>
        </div>

        <div class="io-card">
          <h3>Console da avaliação</h3>
          <pre>{{ latestSubmission.console_output }}</pre>
        </div>
      </section>
    </main>
  </div>
</template>
