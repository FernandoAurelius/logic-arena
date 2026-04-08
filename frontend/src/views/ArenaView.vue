<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { BookOpenText, ChevronRight, Cpu, Flame, LoaderCircle, LogOut, MessageSquare, Play, Send, Terminal, Trophy } from 'lucide-vue-next'
import type { infer as ZodInfer } from 'zod'

import { schemas } from '@/lib/api/generated'
import { exercisesApi, submissionsApi } from '@/lib/api/client'
import MonacoEditor from '@/components/editor/MonacoEditor.vue'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { ScrollArea } from '@/components/ui/scroll-area'
import { useSession } from '@/lib/session'

type ExerciseSummary = ZodInfer<typeof schemas.ExerciseSummarySchema>
type ExerciseDetail = ZodInfer<typeof schemas.ExerciseDetailSchema>
type Submission = ZodInfer<typeof schemas.SubmissionSchema>
type SubmissionSummary = ZodInfer<typeof schemas.SubmissionSummarySchema>
type ReviewChatMessage = ZodInfer<typeof schemas.ReviewChatMessageSchema>

const router = useRouter()
const session = useSession()

const exercises = ref<ExerciseSummary[]>([])
const activeExercise = ref<ExerciseDetail | null>(null)
const submissions = ref<SubmissionSummary[]>([])
const code = ref('')
const latestSubmission = ref<Submission | null>(null)
const isBooting = ref(false)
const isSubmitting = ref(false)
const isChatBusy = ref(false)
const errorMessage = ref('')
const chatOpen = ref(false)
const chatInput = ref('')
const chatMessages = ref<ReviewChatMessage[]>([])
const typingHeat = ref(0)
const confettiBurst = ref(false)

let feedbackPollTimer: number | null = null
let typingCooldownTimer: number | null = null

const activeIndex = computed(() => {
  if (!activeExercise.value) return 0
  return exercises.value.findIndex((exercise) => exercise.slug === activeExercise.value?.slug) + 1
})
const consoleLines = computed(() => {
  if (!latestSubmission.value?.console_output) return ['[INIT] Aguardando execução do módulo atual...']
  return latestSubmission.value.console_output.split('\n').filter(Boolean)
})
const feedbackPayload = computed(() => latestSubmission.value?.feedback_payload ?? null)
const visibleTestCases = computed(() => activeExercise.value?.test_cases ?? [])
const sidebarHistory = computed(() => submissions.value.slice(0, 6))
const isFeedbackPending = computed(() => latestSubmission.value?.feedback_status === 'pending')
const canReviewWithAi = computed(() => Boolean(latestSubmission.value) && !isFeedbackPending.value)
const heatLabel = computed(() => {
  if (typingHeat.value >= 3) return 'Forge em chamas'
  if (typingHeat.value === 2) return 'Ritmo alto'
  if (typingHeat.value === 1) return 'Aquecendo'
  return 'Idle'
})

function stopFeedbackPolling() {
  if (feedbackPollTimer !== null) {
    window.clearInterval(feedbackPollTimer)
    feedbackPollTimer = null
  }
}

function formatSampleBlock(text: string) {
  const normalized = text.replace(/\r/g, '').trim()
  if (!normalized) return ['Sem exemplo disponível.']
  return normalized.split('\n')
}

async function loadExercises() {
  exercises.value = await exercisesApi.get('/api/exercises/', {
    headers: { authorization: session.authHeader() ?? undefined },
  })
  if (!activeExercise.value && exercises.value.length > 0) {
    await selectExercise(exercises.value[0].slug)
  }
}

async function loadSubmissions() {
  submissions.value = await submissionsApi.get('/api/submissions/me', {
    headers: { authorization: session.authHeader() ?? undefined },
  })
}

async function bootstrapArena() {
  errorMessage.value = ''
  isBooting.value = true

  try {
    await Promise.all([loadExercises(), loadSubmissions()])
  } catch (error) {
    console.error(error)
    errorMessage.value = 'Não foi possível carregar a arena autenticada.'
  } finally {
    isBooting.value = false
  }
}

async function selectExercise(slug: string) {
  isBooting.value = true
  errorMessage.value = ''
  stopFeedbackPolling()
  chatOpen.value = false
  chatMessages.value = []

  try {
    const exercise = await exercisesApi.get('/api/exercises/:slug', {
      params: { slug },
      headers: { authorization: session.authHeader() ?? undefined },
    })
    activeExercise.value = exercise
    code.value = exercise.starter_code
    latestSubmission.value = null
  } catch (error) {
    console.error(error)
    errorMessage.value = 'Falha ao carregar os detalhes do exercício.'
  } finally {
    isBooting.value = false
  }
}

async function refreshSubmission(submissionId: number) {
  const refreshed = await submissionsApi.get('/api/submissions/:submission_id', {
    params: { submission_id: submissionId },
    headers: { authorization: session.authHeader() ?? undefined },
  })
  latestSubmission.value = {
    ...refreshed,
    results: refreshed.results.length ? refreshed.results : latestSubmission.value?.results ?? [],
  }
  if (refreshed.feedback_status !== 'pending') {
    stopFeedbackPolling()
    await loadSubmissions()
    if (refreshed.status === 'passed') {
      triggerConfetti()
    }
  }
}

function startFeedbackPolling(submissionId: number) {
  stopFeedbackPolling()
  feedbackPollTimer = window.setInterval(() => {
    void refreshSubmission(submissionId).catch((error) => {
      console.error(error)
      stopFeedbackPolling()
    })
  }, 1500)
}

async function submitSolution() {
  if (!activeExercise.value || !session.token.value) {
    errorMessage.value = 'Faça login antes de submeter uma solução.'
    return
  }

  isSubmitting.value = true
  errorMessage.value = ''
  chatOpen.value = false
  chatMessages.value = []

  try {
    const submission = await submissionsApi.post(
      '/api/submissions/exercises/:slug/submit',
      { source_code: code.value },
      { params: { slug: activeExercise.value.slug }, headers: { authorization: session.authHeader() ?? undefined } },
    )
    latestSubmission.value = submission
    await loadSubmissions()
    if (submission.feedback_status === 'pending') {
      startFeedbackPolling(submission.id)
    }
    if (submission.status === 'passed') {
      triggerConfetti()
    }
  } catch (error) {
    console.error(error)
    errorMessage.value = 'Não foi possível processar a submissão.'
  } finally {
    isSubmitting.value = false
  }
}

async function sendReviewChat() {
  const submission = latestSubmission.value
  if (!submission || !chatInput.value.trim()) return

  const message = chatInput.value.trim()
  chatMessages.value.push({ role: 'user', content: message })
  chatInput.value = ''
  isChatBusy.value = true

  try {
    const response = await submissionsApi.post(
      '/api/submissions/:submission_id/review-chat',
      { message, history: chatMessages.value },
      { params: { submission_id: submission.id }, headers: { authorization: session.authHeader() ?? undefined } },
    )
    chatMessages.value.push({ role: 'assistant', content: response.answer })
  } catch (error) {
    console.error(error)
    chatMessages.value.push({
      role: 'assistant',
      content: 'Não consegui revisar essa dúvida agora. Tente novamente em instantes.',
    })
  } finally {
    isChatBusy.value = false
  }
}

function triggerConfetti() {
  confettiBurst.value = false
  window.setTimeout(() => {
    confettiBurst.value = true
    window.setTimeout(() => {
      confettiBurst.value = false
    }, 2200)
  }, 20)
}

watch(
  code,
  () => {
    typingHeat.value = Math.min(3, typingHeat.value + 1)
    if (typingCooldownTimer !== null) {
      window.clearTimeout(typingCooldownTimer)
    }
    typingCooldownTimer = window.setTimeout(() => {
      typingHeat.value = 0
    }, 1600)
  },
)

function openReviewChat() {
  chatOpen.value = true
  if (chatMessages.value.length === 0 && latestSubmission.value) {
    chatMessages.value = [
      {
        role: 'assistant',
        content: `Vamos revisar essa submissão. Você passou ${latestSubmission.value.passed_tests} de ${latestSubmission.value.total_tests} testes. Me pergunte sobre um erro específico, uma melhoria de código ou o raciocínio esperado.`,
      },
    ]
  }
}

async function logout() {
  stopFeedbackPolling()
  session.clearSession()
  await router.push({ name: 'landing' })
}

onMounted(() => {
  void bootstrapArena()
})

onBeforeUnmount(() => {
  stopFeedbackPolling()
  if (typingCooldownTimer !== null) {
    window.clearTimeout(typingCooldownTimer)
  }
})
</script>

<template>
  <div class="terminal-shell">
    <div v-if="confettiBurst" class="confetti-layer" aria-hidden="true">
      <span v-for="index in 18" :key="index" class="confetti-piece"></span>
    </div>
    <header class="topbar">
      <div class="topbar-left">
        <span class="brand-wordmark">IGNITION_OS</span>
        <nav class="topnav">
          <a class="active" href="#">COMPILER</a>
          <a href="#">ARENA</a>
          <a href="#">RUNNER</a>
        </nav>
      </div>
      <div class="topbar-right">
        <Button variant="outline" size="sm" @click="logout">
          <LogOut :size="14" />
          Sair
        </Button>
        <div class="level-box">
          <strong>LEVEL 42</strong>
          <span>{{ session.currentUser.value?.nickname ?? 'operator' }}</span>
        </div>
        <div class="icon-row">
          <Terminal :size="18" />
          <Cpu :size="18" />
          <Trophy :size="18" />
        </div>
      </div>
    </header>

    <div class="terminal-body">
      <aside class="sidenav">
        <ScrollArea class="sidebar-scroll" viewport-class="sidebar-viewport">
          <div class="sidebar-stack">
            <Card class="operator-card">
              <CardContent class="operator-card-inner">
                <div class="operator-icon">
                  <Cpu :size="18" />
                </div>
                <div>
                  <p class="eyebrow">Operator</p>
                  <strong>{{ session.currentUser.value?.nickname ?? 'OPERATOR_01' }}</strong>
                  <small>STATUS: ROOT_ACCESS</small>
                </div>
              </CardContent>
            </Card>

            <Card class="module-panel">
              <CardHeader>
                <CardTitle>Core Modules</CardTitle>
                <CardDescription>Escolha o exercício que vai simular a rodada atual.</CardDescription>
              </CardHeader>
              <CardContent class="module-list">
                <button
                  v-for="exercise in exercises"
                  :key="exercise.slug"
                  class="module-link"
                  :class="{ active: activeExercise?.slug === exercise.slug }"
                  @click="selectExercise(exercise.slug)"
                >
                  <BookOpenText :size="18" />
                  <div>
                    <strong>{{ exercise.title }}</strong>
                    <small>{{ exercise.difficulty }} · {{ exercise.language }}</small>
                  </div>
                </button>
              </CardContent>
            </Card>

            <Card class="history-panel">
              <CardHeader>
                <CardTitle>History</CardTitle>
                <CardDescription>Últimas execuções persistidas por exercício.</CardDescription>
              </CardHeader>
              <CardContent>
                <ul class="history-list">
                  <li v-for="submission in sidebarHistory" :key="submission.id">
                    <div class="history-line">
                      <strong>{{ submission.exercise_title }}</strong>
                      <Badge :variant="submission.status === 'passed' ? 'default' : 'outline'">
                        {{ submission.status }}
                      </Badge>
                    </div>
                    <span>{{ submission.passed_tests }}/{{ submission.total_tests }} · {{ submission.feedback_status }}</span>
                  </li>
                  <li v-if="sidebarHistory.length === 0" class="dimmed">Nenhuma execução persistida.</li>
                </ul>
              </CardContent>
            </Card>
          </div>
        </ScrollArea>
      </aside>

      <main class="workspace">
        <div class="blueprint-grid"></div>
        <ScrollArea class="workspace-scroll" viewport-class="workspace-viewport">
          <div class="workspace-stack">
            <section class="workspace-header">
              <div>
                <div class="breadcrumb">
                  <span>Programming Logic</span>
                  <ChevronRight :size="14" />
                  <span class="active">{{ activeExercise?.difficulty ?? 'Challenge' }}</span>
                </div>
                <h1>Challenge: {{ activeExercise?.title ?? 'Awaiting Exercise' }}</h1>
                <p class="workspace-copy">
                  {{
                    activeExercise?.statement ??
                    'Selecione um exercício no rail lateral para começar a estação prática.'
                  }}
                </p>
              </div>
              <div class="workspace-status">
                <Badge variant="outline">Quest {{ activeIndex }}/{{ exercises.length || 1 }}</Badge>
                <Badge :variant="isSubmitting || isBooting ? 'dark' : 'default'">
                  {{ isSubmitting ? 'Executing' : isBooting ? 'Loading' : 'Active' }}
                </Badge>
              </div>
            </section>

            <p v-if="errorMessage" class="notice error">{{ errorMessage }}</p>

            <section v-if="activeExercise" class="two-column">
              <div class="left-column">
                <Card class="spec-card">
                  <CardHeader>
                    <CardTitle>Technical Specification</CardTitle>
                    <CardDescription>{{ activeExercise.statement }}</CardDescription>
                  </CardHeader>
                  <CardContent class="spec-content">
                    <div class="formula-box">
                      <p class="section-label">Bank Note</p>
                      <strong>{{ activeExercise.professor_note || 'Sem anotação adicional.' }}</strong>
                    </div>

                    <div class="example-grid">
                      <div class="io-card">
                        <p class="section-label">Input Examples</p>
                        <div class="code-block">
                          <span v-for="(line, index) in formatSampleBlock(activeExercise.sample_input)" :key="`input-${index}`">
                            {{ line }}
                          </span>
                        </div>
                      </div>
                      <div class="io-card">
                        <p class="section-label">Output Examples</p>
                        <div class="code-block">
                          <span v-for="(line, index) in formatSampleBlock(activeExercise.sample_output)" :key="`output-${index}`">
                            {{ line }}
                          </span>
                        </div>
                      </div>
                    </div>

                    <div v-if="visibleTestCases.length" class="visible-tests">
                      <p class="section-label">Visible Tests</p>
                      <div class="test-grid">
                        <div v-for="testCase in visibleTestCases" :key="testCase.id" class="test-card">
                          <strong>Teste {{ testCase.id }}</strong>
                          <div class="test-case-line">
                            <span>Entrada</span>
                            <code>{{ testCase.input_data }}</code>
                          </div>
                          <div class="test-case-line">
                            <span>Saída</span>
                            <code>{{ testCase.expected_output }}</code>
                          </div>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>

              <div class="right-column">
                <Card class="editor-card editor-card--compact">
                  <CardContent class="editor-content editor-content--flush">
                    <MonacoEditor
                      v-model="code"
                      class="code-editor"
                      language="python"
                      height="36rem"
                      :read-only="isSubmitting"
                    />
                  </CardContent>
                  <CardFooter class="editor-footer">
                    <Button :disabled="isSubmitting || isBooting" @click="submitSolution">
                      <Play :size="16" />
                      {{ isSubmitting ? 'Executando...' : 'Executar módulo' }}
                    </Button>
                    <Button variant="outline" :disabled="!canReviewWithAi || isChatBusy" @click="openReviewChat">
                      <MessageSquare :size="16" />
                      Revisar com IA
                    </Button>
                    <span class="editor-helper">
                      {{ isFeedbackPending ? 'Execução concluída · revisão com IA em andamento' : 'Runner isolado · revisão com IA disponível' }}
                    </span>
                    <div class="typing-heat" :data-level="typingHeat">
                      <Flame :size="16" />
                      <span>{{ heatLabel }}</span>
                    </div>
                  </CardFooter>
                </Card>

                <Card class="console-card">
                  <CardHeader class="console-header">
                    <div class="console-heading">
                      <Terminal :size="16" />
                      <CardTitle>Console Output</CardTitle>
                    </div>
                    <Badge :variant="latestSubmission?.status === 'passed' ? 'default' : 'outline'">
                      {{ latestSubmission?.status ?? 'idle' }}
                    </Badge>
                  </CardHeader>
                  <CardContent class="console-content">
                    <div class="console-body">
                      <div v-for="(line, index) in consoleLines" :key="`${index}-${line}`" class="console-line">
                        <span class="console-time">{{ String(index).padStart(2, '0') }}:42</span>
                        <span :class="line.includes('PASSOU') ? 'tag pass' : line.includes('FALHOU') ? 'tag fail' : 'tag exec'">
                          {{ line.includes('PASSOU') ? '[PASS]' : line.includes('FALHOU') ? '[FAIL]' : '[EXEC]' }}
                        </span>
                        <span>{{ line }}</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <section v-if="latestSubmission" class="submission-review-grid">
                  <Card class="feedback-card">
                    <CardHeader>
                      <div class="feedback-header">
                        <div>
                          <p class="eyebrow">Submission</p>
                          <CardTitle>{{ latestSubmission.passed_tests }}/{{ latestSubmission.total_tests }} testes</CardTitle>
                        </div>
                        <div class="feedback-badges">
                          <Badge>{{ latestSubmission.status }}</Badge>
                          <Badge variant="outline">{{ latestSubmission.feedback_status }}</Badge>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent class="feedback-grid feedback-grid--stacked">
                      <div class="feedback-column">
                        <p class="section-label">Resumo</p>
                        <p>{{ feedbackPayload?.summary ?? latestSubmission.feedback }}</p>
                      </div>
                      <div class="feedback-column">
                        <p class="section-label">Pontos fortes</p>
                        <ul>
                          <li v-for="item in feedbackPayload?.strengths ?? []" :key="item">{{ item }}</li>
                        </ul>
                      </div>
                      <div class="feedback-column">
                        <p class="section-label">Ajustes</p>
                        <ul>
                          <li v-for="item in feedbackPayload?.issues ?? []" :key="item">{{ item }}</li>
                        </ul>
                      </div>
                      <div class="feedback-column">
                        <p class="section-label">Próximos passos</p>
                        <ul>
                          <li v-for="item in feedbackPayload?.next_steps ?? []" :key="item">{{ item }}</li>
                        </ul>
                      </div>
                    </CardContent>
                  </Card>

                  <Card v-if="chatOpen && latestSubmission" class="review-chat-card">
                    <CardHeader>
                      <div class="feedback-header">
                        <div>
                          <p class="eyebrow">IA Review</p>
                          <CardTitle>Conversar sobre a submissão</CardTitle>
                        </div>
                        <Badge variant="outline">{{ latestSubmission.feedback_source }}</Badge>
                      </div>
                    </CardHeader>
                    <CardContent class="review-chat-content">
                      <div class="review-chat-log">
                        <article
                          v-for="(message, index) in chatMessages"
                          :key="`${message.role}-${index}`"
                          class="review-chat-message"
                          :class="message.role"
                        >
                          <strong>{{ message.role === 'assistant' ? 'IA' : 'Você' }}</strong>
                          <p>{{ message.content }}</p>
                        </article>
                        <div v-if="isChatBusy" class="review-chat-message assistant">
                          <strong>IA</strong>
                          <p><LoaderCircle class="inline-loader" :size="16" /> Revisando sua dúvida...</p>
                        </div>
                      </div>
                      <div class="review-chat-form">
                        <textarea
                          v-model="chatInput"
                          class="review-chat-input"
                          rows="3"
                          placeholder="Pergunte por que falhou, como melhorar a solução ou qual raciocínio a banca esperava."
                        ></textarea>
                        <div class="review-chat-actions">
                          <Button :disabled="isChatBusy || !chatInput.trim()" @click="sendReviewChat">
                            <Send :size="16" />
                            Enviar
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </section>
              </div>
            </section>
          </div>
        </ScrollArea>
      </main>
    </div>
  </div>
</template>
