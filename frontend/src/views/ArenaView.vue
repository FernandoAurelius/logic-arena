<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { BookOpenText, ChevronRight, FileText, FlaskConical, ListChecks, LogOut, MessageSquare, Play, UserRound } from 'lucide-vue-next'
import type { infer as ZodInfer } from 'zod'

import { schemas } from '@/shared/api/generated'
import { submissionApi } from '@/entities/submission/api/submission.api'
import ArenaResultsDialog from '@/components/arena/ArenaResultsDialog.vue'
import ArenaSidebar from '@/components/arena/ArenaSidebar.vue'
import MonacoEditor from '@/components/editor/MonacoEditor.vue'
import ProfileModal from '@/components/theme/ProfileModal.vue'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { useSession } from '@/entities/session'
import { useArenaExerciseWorkspace } from '@/features/arena/open-exercise/model/useArenaExerciseWorkspace'

type Submission = ZodInfer<typeof schemas.SubmissionSchema>
type SubmissionSummary = ZodInfer<typeof schemas.SubmissionSummarySchema>

const router = useRouter()
const route = useRoute()
const session = useSession()

const isSubmitting = ref(false)
const isChatBusy = ref(false)
const hintsOpen = ref(false)
const chatInput = ref('')
const confettiBurst = ref(false)
const levelUpBurst = ref(false)
const showProfile = ref(false)
const resultsDialogOpen = ref(false)
const resultsTab = ref<'saida' | 'testes' | 'revisao' | 'chat'>('saida')
const specTab = ref<'descricao' | 'exemplos' | 'testes'>('descricao')

let feedbackPollTimer: number | null = null
let levelUpTimer: number | null = null

const {
  exercises,
  activeExercise,
  trackContext,
  code,
  latestSubmission,
  chatMessages,
  isBooting,
  errorMessage,
  restoreDialogOpen,
  pendingRestoreSubmission,
  rememberRestoreChoice,
  routeTrackSlug,
  groupedExercises,
  trackExercises,
  activeTrackIndex,
  previousTrackExercise,
  nextTrackExercise,
  sidebarHistory,
  bootstrapArena,
  loadTrackContext,
  loadSubmissions,
  selectExercise: selectExerciseFromWorkspace,
  navigateTrackExercise: navigateTrackExerciseFromWorkspace,
  openSubmissionSession: openSubmissionSessionFromWorkspace,
  setHydratedSubmission,
  confirmRestoreSubmission: confirmRestoreSubmissionFromWorkspace,
  declineRestoreSubmission: declineRestoreSubmissionFromWorkspace,
  handleRestoreDialogOpen: handleRestoreDialogOpenFromWorkspace,
} = useArenaExerciseWorkspace({
  authHeader: () => session.authHeader(),
  onSubmissionHydrated: applySubmissionProgress,
  onStopFeedbackPolling: stopFeedbackPolling,
  onStartFeedbackPolling: (submissionId) => startFeedbackPolling(submissionId),
})

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
const isFeedbackPending = computed(() => latestSubmission.value?.feedback_status === 'pending')
const canReviewWithAi = computed(() => Boolean(latestSubmission.value) && !isFeedbackPending.value)
const level = computed(() => session.currentUser.value?.level ?? 1)
const xpIntoLevel = computed(() => session.currentUser.value?.xp_into_level ?? 0)
const xpProgress = computed(() => Math.min(100, Math.max(0, xpIntoLevel.value)))
const xpToNextLevel = computed(() => session.currentUser.value?.xp_to_next_level ?? 100)
const progressRewards = computed(() => latestSubmission.value?.unlocked_progress_rewards ?? [])
const submissionOutcomeTone = computed(() => {
  if (!latestSubmission.value) return 'idle'
  if (latestSubmission.value.status === 'passed' && latestSubmission.value.xp_awarded > 0) return 'reward'
  if (latestSubmission.value.status === 'passed') return 'pass'
  return 'fail'
})
const submissionOutcomeTitle = computed(() => {
  if (!latestSubmission.value) return 'Aguardando execução'
  if (latestSubmission.value.status === 'passed' && latestSubmission.value.xp_awarded > 0) return 'Passou e evoluiu'
  if (latestSubmission.value.status === 'passed') return 'Passou, mas sem novo XP'
  return 'Ainda não passou'
})
const submissionOutcomeCopy = computed(() => {
  if (!latestSubmission.value) return 'Execute um exercício para receber o diagnóstico desta rodada.'
  if (latestSubmission.value.status === 'passed' && latestSubmission.value.xp_awarded > 0) {
    return 'Você concluiu o exercício e desbloqueou um marco real de progresso.'
  }
  if (latestSubmission.value.status === 'passed') {
    return 'A solução está correta, mas esta rodada não mudou seu estado estrutural de progresso.'
  }
  return 'A rodada ainda precisa de ajuste. Use o console e a revisão com IA para entender onde corrigir.'
})
const rewardSummary = computed(() => {
  const submission = latestSubmission.value
  if (!submission) return ''
  if (submission.xp_awarded > 0 && progressRewards.value.length > 0) {
    const labels = progressRewards.value.map((reward) => reward.label).join(', ')
    return `${labels}: +${submission.xp_awarded} XP`
  }
  if (submission.xp_awarded > 0) {
    return `+${submission.xp_awarded} XP nesta rodada`
  }
  return 'Sem ganho de XP nesta rodada'
})

function triggerLevelUp() {
  levelUpBurst.value = true
  if (levelUpTimer !== null) {
    window.clearTimeout(levelUpTimer)
  }
  levelUpTimer = window.setTimeout(() => {
    levelUpBurst.value = false
  }, 2600)
}

function applySubmissionProgress(submission: Submission) {
  const previousLevel = session.currentUser.value?.level ?? 1
  session.mergeCurrentUserProgress(submission.user_progress)
  if (submission.user_progress.level > previousLevel) {
    triggerLevelUp()
    triggerConfetti()
  }
}

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

function traduzirStatusExecucao(status?: string) {
  switch (status) {
    case 'passed':
      return 'Aprovada'
    case 'failed':
      return 'Reprovada'
    case 'error':
      return 'Erro'
    case 'pending':
      return 'Pendente'
    default:
      return 'Inativa'
  }
}

function traduzirEstadoArena() {
  if (isSubmitting.value) return 'Executando'
  if (isBooting.value) return 'Carregando'
  return 'Pronta'
}

function abrirCentralDeResultado(tab: 'saida' | 'testes' | 'revisao' | 'chat' = 'saida') {
  resultsTab.value = tab
  resultsDialogOpen.value = true
}

function resetArenaPanels() {
  resultsDialogOpen.value = false
  hintsOpen.value = false
}

async function handleSelectExercise(slug: string) {
  resetArenaPanels()
  await selectExerciseFromWorkspace(slug)
}

function navigateTrackExercise(direction: 'previous' | 'next') {
  resetArenaPanels()
  navigateTrackExerciseFromWorkspace(direction)
}

async function handleOpenSubmissionSession(submissionSummary: SubmissionSummary) {
  resetArenaPanels()
  await openSubmissionSessionFromWorkspace(submissionSummary)
}

async function confirmRestoreSubmission() {
  await confirmRestoreSubmissionFromWorkspace()
  resultsDialogOpen.value = false
}

function declineRestoreSubmission() {
  declineRestoreSubmissionFromWorkspace()
  resultsDialogOpen.value = false
}

function handleRestoreDialogOpen(nextOpen: boolean) {
  handleRestoreDialogOpenFromWorkspace(nextOpen)
}

async function refreshSubmission(submissionId: number) {
  const refreshed = await submissionApi.getById(submissionId, session.authHeader() ?? undefined)
  latestSubmission.value = {
    ...refreshed,
    results: refreshed.results.length ? refreshed.results : latestSubmission.value?.results ?? [],
  }
  applySubmissionProgress(refreshed)
  if ((refreshed.review_chat_history?.length ?? 0) > 0) {
    chatMessages.value = refreshed.review_chat_history
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
  resultsDialogOpen.value = false
  chatMessages.value = []

  try {
    const submission = await submissionApi.submit(activeExercise.value.slug, code.value, session.authHeader() ?? undefined)
    setHydratedSubmission(submission)
    pendingRestoreSubmission.value = null
    restoreDialogOpen.value = false
    applySubmissionProgress(submission)
    await loadSubmissions()
    if (submission.status === 'passed') {
      triggerConfetti()
    }
    abrirCentralDeResultado('saida')
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
    const response = await submissionApi.sendReviewChat(
      submission.id,
      message,
      chatMessages.value,
      session.authHeader() ?? undefined,
    )
    chatMessages.value.push({ role: 'assistant', content: response.answer })
    if (latestSubmission.value) {
      latestSubmission.value.review_chat_history = [...chatMessages.value]
    }
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
  () => route.query.track,
  (trackSlug) => {
    void loadTrackContext(typeof trackSlug === 'string' ? trackSlug : null)
  },
)

watch(
  () => route.query.exercise,
  (exerciseSlug) => {
    if (typeof exerciseSlug !== 'string' || !exerciseSlug || activeExercise.value?.slug === exerciseSlug) {
      return
    }
    if (exercises.value.some((exercise) => exercise.slug === exerciseSlug)) {
      void handleSelectExercise(exerciseSlug)
    }
  },
)

function openReviewChat() {
  if (chatMessages.value.length === 0 && latestSubmission.value) {
    chatMessages.value = [
      {
        role: 'assistant',
        content: `Vamos revisar essa submissão. Você passou ${latestSubmission.value.passed_tests} de ${latestSubmission.value.total_tests} testes. Me pergunte sobre um erro específico, uma melhoria de código ou o raciocínio esperado.`,
      },
    ]
  }
  abrirCentralDeResultado('chat')
}

function toggleHints() {
  hintsOpen.value = !hintsOpen.value
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
  if (levelUpTimer !== null) {
    window.clearTimeout(levelUpTimer)
  }
})
</script>

<template>
  <div class="terminal-shell">
    <div v-if="confettiBurst" class="confetti-layer" aria-hidden="true">
      <span v-for="index in 18" :key="index" class="confetti-piece"></span>
    </div>
    <div v-if="levelUpBurst" class="levelup-banner" aria-hidden="true">
      <span class="levelup-eyebrow">SUBIU DE NÍVEL</span>
      <strong>Você avançou para o nível {{ level }}</strong>
    </div>
    <header class="topbar">
      <div class="topbar-left">
        <span class="brand-wordmark">LOGIC ARENA</span>
        <nav class="workspace-nav">
          <button class="workspace-nav-link" type="button" @click="router.push({ name: 'navigator' })">Navegador</button>
          <button class="workspace-nav-link workspace-nav-link--active" type="button">Arena</button>
          <button
            v-if="typeof route.query.track === 'string'"
            class="workspace-nav-link"
            type="button"
            @click="router.push({ name: 'track', params: { trackSlug: route.query.track } })"
          >
            Trilha
          </button>
        </nav>
      </div>
      <div class="topbar-right">
        <div class="topbar-status">
          <div class="level-box" :class="{ 'level-box--up': levelUpBurst }">
            <strong>NÍVEL {{ level }}</strong>
            <span>{{ session.currentUser.value?.nickname ?? 'operador' }}</span>
            <small>{{ xpIntoLevel }}/100 XP · faltam {{ xpToNextLevel }} XP</small>
            <div class="level-track">
              <div class="level-track-fill" :style="{ width: `${xpProgress}%` }"></div>
            </div>
          </div>
        </div>
        <div class="topbar-actions">
          <Button variant="outline" size="sm" @click="showProfile = true">
            <UserRound :size="14" />
            Perfil
          </Button>
          <Button variant="outline" size="sm" @click="logout">
            <LogOut :size="14" />
            Sair
          </Button>
        </div>
      </div>
    </header>

    <div class="terminal-body terminal-body--arena">
      <ArenaSidebar
        :grouped-exercises="groupedExercises"
        :active-exercise-slug="activeExercise?.slug ?? null"
        :sidebar-history="sidebarHistory"
        :latest-submission-id="latestSubmission?.id ?? null"
        :route-track-slug="routeTrackSlug"
        :track-name="trackContext?.name ?? activeExercise?.track_name ?? activeExercise?.module_name ?? null"
        :can-go-previous="Boolean(previousTrackExercise)"
        :can-go-next="Boolean(nextTrackExercise)"
        @select-exercise="handleSelectExercise"
        @open-history="handleOpenSubmissionSession"
        @go-track="router.push({ name: 'track', params: { trackSlug: routeTrackSlug } })"
        @go-navigator="router.push({ name: 'navigator' })"
        @navigate-track="navigateTrackExercise"
      />

      <main class="workspace">
        <div class="blueprint-grid"></div>
        <ScrollArea class="workspace-scroll" viewport-class="workspace-viewport">
          <div class="workspace-stack">
            <p v-if="errorMessage" class="notice error">{{ errorMessage }}</p>

            <div v-if="activeExercise" class="arena-toolbar">
              <div class="arena-toolbar__left">
                <Button variant="outline" size="sm" @click="toggleHints">
                  <BookOpenText :size="16" />
                  Dicas
                </Button>
                <Button v-if="latestSubmission" variant="outline" size="sm" :disabled="!canReviewWithAi || isChatBusy" @click="openReviewChat">
                  <MessageSquare :size="16" />
                  Chat da revisão
                </Button>
              </div>
              <div v-if="latestSubmission" class="arena-toolbar__center">
                <div class="spec-outcome-banner spec-outcome-banner--toolbar" :data-tone="submissionOutcomeTone">
                  <div class="spec-outcome-banner__status">
                    <Badge>{{ traduzirStatusExecucao(latestSubmission.status) }}</Badge>
                    <div class="spec-outcome-banner__copy">
                      <strong>{{ submissionOutcomeTitle }}</strong>
                      <span>{{ latestSubmission.passed_tests }}/{{ latestSubmission.total_tests }} testes · {{ rewardSummary }}</span>
                    </div>
                  </div>
                  <div class="spec-outcome-banner__actions">
                    <Button variant="outline" size="sm" @click="abrirCentralDeResultado('saida')">Abrir central</Button>
                  </div>
                </div>
              </div>
              <div class="arena-toolbar__right">
                <Button size="sm" :disabled="isSubmitting || isBooting" @click="submitSolution">
                  <Play :size="16" />
                  {{ isSubmitting ? 'Executando...' : 'Executar' }}
                </Button>
              </div>
            </div>

            <section v-if="activeExercise" class="two-column">
              <div class="left-column">
                <Card class="spec-card">
                  <CardHeader class="spec-card-header">
                    <Tabs v-model:model-value="specTab" class="spec-tabs">
                      <TabsList class="spec-tabs-list">
                        <TabsTrigger value="descricao" class="spec-tabs-trigger">
                          <FileText :size="15" />
                          Especificação
                        </TabsTrigger>
                        <TabsTrigger value="exemplos" class="spec-tabs-trigger">
                          <FlaskConical :size="15" />
                          Exemplos
                        </TabsTrigger>
                        <TabsTrigger value="testes" class="spec-tabs-trigger">
                          <ListChecks :size="15" />
                          Testes
                        </TabsTrigger>
                      </TabsList>
                    </Tabs>
                    <div class="spec-heading-block">
                      <div class="breadcrumb">
                        <button class="breadcrumb-link" type="button" @click="router.push({ name: 'navigator' })">Navegador</button>
                        <ChevronRight :size="14" />
                        <button
                          v-if="routeTrackSlug"
                          class="breadcrumb-link"
                          type="button"
                          @click="router.push({ name: 'track', params: { trackSlug: routeTrackSlug } })"
                        >
                          {{ activeExercise?.track_name ?? 'Trilha' }}
                        </button>
                        <template v-if="routeTrackSlug">
                          <ChevronRight :size="14" />
                        </template>
                        <button
                          v-else-if="activeExercise?.module_name"
                          class="breadcrumb-link"
                          type="button"
                          @click="router.push({ name: 'navigator' })"
                        >
                          {{ activeExercise.module_name }}
                        </button>
                        <template v-if="!routeTrackSlug && activeExercise?.module_name">
                          <ChevronRight :size="14" />
                        </template>
                        <span class="active">{{ activeExercise?.difficulty ?? 'Exercício' }}</span>
                      </div>
                      <h1 class="spec-heading-title">{{ activeExercise?.title ?? 'Aguardando exercício' }}</h1>
                      <div class="challenge-meta challenge-meta--compact">
                        <Badge variant="outline">{{ activeExercise.module_name ?? 'Sem módulo' }}</Badge>
                        <Badge variant="outline">{{ activeExercise.track_name ?? 'Sem trilha' }}</Badge>
                        <Badge variant="outline">{{ activeExercise.difficulty }}</Badge>
                        <Badge variant="outline">Questão {{ activeIndex }}/{{ exercises.length || 1 }}</Badge>
                        <Badge :variant="isSubmitting || isBooting ? 'dark' : 'default'">
                          {{ traduzirEstadoArena() }}
                        </Badge>
                      </div>
                      <div v-if="routeTrackSlug && trackContext" class="workspace-track-inline">
                        <span class="workspace-track-inline__label">
                          {{ trackContext.name }}
                          <small>
                            {{
                              activeTrackIndex >= 0
                                ? `Etapa ${activeTrackIndex + 1} de ${trackExercises.length}`
                                : 'Contexto de trilha ativo'
                            }}
                          </small>
                        </span>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent class="spec-content">
                    <Tabs v-model:model-value="specTab" class="spec-tabs-content">
                      <TabsContent value="descricao" class="spec-pane">
                        <div class="formula-box formula-box--statement">
                          <p class="section-label">Enunciado</p>
                          <p>{{ activeExercise.statement }}</p>
                        </div>

                        <div class="formula-box">
                          <p class="section-label">Modo de prova</p>
                          <strong>Resolva sem código inicial. Abra <em>dicas</em> apenas se quiser uma pista opcional.</strong>
                        </div>

                        <div v-if="routeTrackSlug && trackContext && activeTrackIndex >= 0" class="formula-box formula-box--track">
                          <p class="section-label">Posição na trilha</p>
                          <strong>{{ trackContext.name }} · etapa {{ activeTrackIndex + 1 }}</strong>
                          <p>
                            {{
                              trackExercises[activeTrackIndex]?.pedagogical_brief ??
                              'Este exercício faz parte de um percurso estruturado de progressão.'
                            }}
                          </p>
                        </div>
                      </TabsContent>

                      <TabsContent value="exemplos" class="spec-pane spec-pane--examples">
                        <div class="example-flow-grid">
                          <div class="example-flow-card io-card">
                            <p class="section-label">Exemplo de entrada</p>
                            <div class="code-block">
                              <span v-for="(line, index) in formatSampleBlock(activeExercise.sample_input)" :key="`input-${index}`">
                                {{ line }}
                              </span>
                            </div>
                          </div>
                          <div class="example-flow-arrow" aria-hidden="true">
                            <ChevronRight :size="18" />
                          </div>
                          <div class="example-flow-card io-card">
                            <p class="section-label">Exemplo de saída</p>
                            <div class="code-block">
                              <span v-for="(line, index) in formatSampleBlock(activeExercise.sample_output)" :key="`output-${index}`">
                                {{ line }}
                              </span>
                            </div>
                          </div>
                        </div>
                      </TabsContent>

                      <TabsContent value="testes" class="spec-pane">
                        <div v-if="visibleTestCases.length" class="visible-tests">
                          <p class="section-label">Testes</p>
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
                        <div v-else class="formula-box">
                          <p class="section-label">Testes</p>
                          <p>Este exercício não expõe testes visíveis nesta rodada.</p>
                        </div>
                      </TabsContent>
                    </Tabs>
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
                      height="calc(100vh - 15.5rem)"
                      :read-only="isSubmitting"
                      placeholder="# escreva sua solução aqui"
                    />
                  </CardContent>
                </Card>
              </div>
            </section>
          </div>
        </ScrollArea>
      </main>
    </div>
    <ArenaResultsDialog
      :open="resultsDialogOpen"
      :tab="resultsTab"
      :active-exercise-title="activeExercise?.title ?? ''"
      :submission="latestSubmission"
      :console-lines="consoleLines"
      :submission-outcome-tone="submissionOutcomeTone"
      :submission-outcome-title="submissionOutcomeTitle"
      :submission-outcome-copy="submissionOutcomeCopy"
      :reward-summary="rewardSummary"
      :progress-rewards="progressRewards"
      :feedback-payload="feedbackPayload"
      :chat-messages="chatMessages"
      :chat-input="chatInput"
      :is-chat-busy="isChatBusy"
      @update:open="resultsDialogOpen = $event"
      @update:tab="resultsTab = $event"
      @update:chat-input="chatInput = $event"
      @send-chat="sendReviewChat"
    />
    <Dialog :open="restoreDialogOpen" @update:open="handleRestoreDialogOpen">
      <DialogContent class="arena-confirm-dialog" :show-close="true">
        <DialogHeader>
          <DialogTitle>Restaurar última submissão?</DialogTitle>
          <DialogDescription>
            Encontramos uma tentativa anterior sua para
            <strong>{{ pendingRestoreSubmission?.exercise_title ?? activeExercise?.title ?? 'este exercício' }}</strong>.
          </DialogDescription>
        </DialogHeader>
        <div class="hint-content">
          <div class="hint-block">
            <p class="section-label">Escolha como abrir</p>
            <p>Você pode continuar da sua última submissão salva ou começar com o editor totalmente em branco.</p>
          </div>
          <label class="remember-choice-row">
            <input v-model="rememberRestoreChoice" type="checkbox" />
            <span>Lembrar minha resposta</span>
          </label>
        </div>
        <div class="arena-confirm-dialog__actions">
          <Button variant="outline" @click="declineRestoreSubmission">Começar em branco</Button>
          <Button @click="confirmRestoreSubmission">Abrir última submissão</Button>
        </div>
      </DialogContent>
    </Dialog>
    <Dialog :open="hintsOpen" @update:open="hintsOpen = $event">
      <DialogContent class="hint-dialog" :show-close="true">
        <DialogHeader>
          <DialogTitle>Dicas</DialogTitle>
          <DialogDescription>Pistas opcionais para destravar o raciocínio sem entregar a solução.</DialogDescription>
        </DialogHeader>
        <div class="hint-content">
          <div class="hint-block">
            <p class="section-label">Pista do professor</p>
            <p>{{ activeExercise?.professor_note || 'Sem hint adicional para este exercício.' }}</p>
          </div>
          <div class="hint-block">
            <p class="section-label">Estratégia</p>
            <ul>
              <li>Separe o problema em entrada, processamento e saída antes de codar.</li>
              <li>Use o exemplo visível para validar o fluxo mínimo.</li>
              <li>Pense em um caso limite simples antes de submeter.</li>
            </ul>
          </div>
        </div>
      </DialogContent>
    </Dialog>
    <ProfileModal v-if="showProfile" @close="showProfile = false" />
  </div>
</template>
