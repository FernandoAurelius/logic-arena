<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { LogOut, UserRound } from 'lucide-vue-next'
import type { infer as ZodInfer } from 'zod'

import { schemas } from '@/shared/api/generated'
import ArenaResultsDialog from '@/components/arena/ArenaResultsDialog.vue'
import ArenaSidebar from '@/components/arena/ArenaSidebar.vue'
import MonacoEditor from '@/components/editor/MonacoEditor.vue'
import ProfileModal from '@/components/theme/ProfileModal.vue'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { ScrollArea } from '@/components/ui/scroll-area'
import { useSession } from '@/entities/session'
import { useArenaExerciseWorkspace } from '@/features/arena/open-exercise/model/useArenaExerciseWorkspace'
import { useArenaSubmissionFlow } from '@/features/arena/submission/model/useArenaSubmissionFlow'
import ArenaToolbar from '@/widgets/arena/ArenaToolbar.vue'
import ArenaSpecPanel from '@/widgets/arena/ArenaSpecPanel.vue'

type Submission = ZodInfer<typeof schemas.SubmissionSchema>
type SubmissionSummary = ZodInfer<typeof schemas.SubmissionSummarySchema>

const router = useRouter()
const route = useRoute()
const session = useSession()

const hintsOpen = ref(false)
const chatInput = ref('')
const confettiBurst = ref(false)
const levelUpBurst = ref(false)
const showProfile = ref(false)
const specTab = ref<'descricao' | 'exemplos' | 'testes'>('descricao')

let levelUpTimer: number | null = null
let submissionFlowRef: ReturnType<typeof useArenaSubmissionFlow> | null = null

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
  onStopFeedbackPolling: () => submissionFlowRef?.stopFeedbackPolling(),
  onStartFeedbackPolling: (submissionId) => submissionFlowRef?.startFeedbackPolling(submissionId),
})

const activeIndex = computed(() => {
  if (!activeExercise.value) return 0
  return exercises.value.findIndex((exercise) => exercise.slug === activeExercise.value?.slug) + 1
})
const visibleTestCases = computed(() => activeExercise.value?.test_cases ?? [])
const level = computed(() => session.currentUser.value?.level ?? 1)
const xpIntoLevel = computed(() => session.currentUser.value?.xp_into_level ?? 0)
const xpProgress = computed(() => Math.min(100, Math.max(0, xpIntoLevel.value)))
const xpToNextLevel = computed(() => session.currentUser.value?.xp_to_next_level ?? 100)

const submissionFlow = useArenaSubmissionFlow({
  authHeader: () => session.authHeader(),
  activeExerciseSlug: computed(() => activeExercise.value?.slug ?? null),
  code,
  latestSubmission,
  chatMessages,
  onSubmissionHydrated: setHydratedSubmission,
  onSubmissionProgress: applySubmissionProgress,
  onSubmissionPassed: () => triggerConfetti(),
  onReloadSubmissions: loadSubmissions,
})
submissionFlowRef = submissionFlow

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

function resetArenaPanels() {
  submissionFlow.resultsDialogOpen.value = false
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
  submissionFlow.resultsDialogOpen.value = false
}

function declineRestoreSubmission() {
  declineRestoreSubmissionFromWorkspace()
  submissionFlow.resultsDialogOpen.value = false
}

function handleRestoreDialogOpen(nextOpen: boolean) {
  handleRestoreDialogOpenFromWorkspace(nextOpen)
}

async function submitSolution() {
  if (!activeExercise.value || !session.token.value) {
    errorMessage.value = 'Faça login antes de submeter uma solução.'
    return
  }

  errorMessage.value = ''

  try {
    pendingRestoreSubmission.value = null
    restoreDialogOpen.value = false
    await submissionFlow.submitSolution()
  } catch (error) {
    console.error(error)
    errorMessage.value = 'Não foi possível processar a submissão.'
  }
}

async function sendReviewChat() {
  await submissionFlow.sendReviewChat(chatInput)
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
  submissionFlow.openReviewChat()
}

function toggleHints() {
  hintsOpen.value = !hintsOpen.value
}

async function logout() {
  submissionFlow.stopFeedbackPolling()
  session.clearSession()
  await router.push({ name: 'landing' })
}

onMounted(() => {
  void bootstrapArena()
})

onBeforeUnmount(() => {
  submissionFlow.stopFeedbackPolling()
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

            <ArenaToolbar
              v-if="activeExercise"
              :has-submission="Boolean(latestSubmission)"
              :can-review-with-ai="submissionFlow.canReviewWithAi.value"
              :is-chat-busy="submissionFlow.isChatBusy.value"
              :is-submitting="submissionFlow.isSubmitting.value"
              :is-booting="isBooting"
              :latest-submission-status="latestSubmission?.status"
              :latest-submission-passed-tests="latestSubmission?.passed_tests"
              :latest-submission-total-tests="latestSubmission?.total_tests"
              :submission-outcome-tone="submissionFlow.submissionOutcomeTone.value"
              :submission-outcome-title="submissionFlow.submissionOutcomeTitle.value"
              :reward-summary="submissionFlow.rewardSummary.value"
              @toggle-hints="toggleHints"
              @open-review-chat="openReviewChat"
              @open-results="submissionFlow.openResultsCenter('saida')"
              @submit="submitSolution"
            />

            <section v-if="activeExercise" class="two-column">
              <div class="left-column">
                <ArenaSpecPanel
                  :spec-tab="specTab"
                  :route-track-slug="routeTrackSlug"
                  :active-exercise="activeExercise"
                  :active-index="activeIndex"
                  :exercise-count="exercises.length"
                  :is-submitting="submissionFlow.isSubmitting.value"
                  :is-booting="isBooting"
                  :track-name="trackContext?.name ?? null"
                  :active-track-index="activeTrackIndex"
                  :track-exercise-count="trackExercises.length"
                  :active-track-brief="activeTrackIndex >= 0 ? trackExercises[activeTrackIndex]?.pedagogical_brief ?? null : null"
                  :visible-test-cases="visibleTestCases"
                  @update:spec-tab="specTab = $event"
                  @go-navigator="router.push({ name: 'navigator' })"
                  @go-track="router.push({ name: 'track', params: { trackSlug: routeTrackSlug } })"
                />
              </div>

              <div class="right-column">
                <Card class="editor-card editor-card--compact">
                  <CardContent class="editor-content editor-content--flush">
                    <MonacoEditor
                      v-model="code"
                      class="code-editor"
                      language="python"
                      height="calc(100vh - 15.5rem)"
                      :read-only="submissionFlow.isSubmitting.value"
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
      :open="submissionFlow.resultsDialogOpen.value"
      :tab="submissionFlow.resultsTab.value"
      :active-exercise-title="activeExercise?.title ?? ''"
      :submission="latestSubmission"
      :console-lines="submissionFlow.consoleLines.value"
      :submission-outcome-tone="submissionFlow.submissionOutcomeTone.value"
      :submission-outcome-title="submissionFlow.submissionOutcomeTitle.value"
      :submission-outcome-copy="submissionFlow.submissionOutcomeCopy.value"
      :reward-summary="submissionFlow.rewardSummary.value"
      :progress-rewards="submissionFlow.progressRewards.value"
      :feedback-payload="submissionFlow.feedbackPayload.value"
      :chat-messages="chatMessages"
      :chat-input="chatInput"
      :is-chat-busy="submissionFlow.isChatBusy.value"
      @update:open="submissionFlow.resultsDialogOpen.value = $event"
      @update:tab="submissionFlow.resultsTab.value = $event"
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
