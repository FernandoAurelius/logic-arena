<script setup lang="ts">
import '@/styles/catalog.css'
import '@/pages/arena/style.css'
import { LogOut, UserRound } from 'lucide-vue-next'

import ArenaResultsDialog from '@/widgets/arena/ArenaResultsDialog.vue'
import ArenaSidebar from '@/widgets/arena/ArenaSidebar.vue'
import ProfileModal from '@/widgets/profile/ProfileModal.vue'
import { Button } from '@/shared/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/shared/ui/dialog'
import { ScrollArea } from '@/shared/ui/scroll-area'
import { useArenaPage } from '@/pages/arena/model/useArenaPage'
import ArenaToolbar from '@/widgets/arena/ArenaToolbar.vue'
import ArenaSpecPanel from '@/widgets/arena/ArenaSpecPanel.vue'
import ArenaSurfaceHost from '@/widgets/arena/ArenaSurfaceHost.vue'

const {
  session,
  hintsOpen,
  chatInput,
  confettiBurst,
  levelUpBurst,
  showProfile,
  specTab,
  routeTrackSlug,
  exercises,
  activeExercise,
  activeSessionConfig,
  trackContext,
  code,
  selectedOptions,
  responseText,
  latestSubmission,
  chatMessages,
  isBooting,
  errorMessage,
  restoreDialogOpen,
  pendingRestoreSubmission,
  rememberRestoreChoice,
  groupedExercises,
  trackExercises,
  activeIndex,
  visibleTestCases,
  level,
  xpProgress,
  xpIntoLevel,
  xpToNextLevel,
  activeTrackIndex,
  previousTrackExercise,
  nextTrackExercise,
  sidebarHistory,
  submissionFlow,
  selectExercise,
  navigateTrackExercise,
  openSubmissionSession,
  confirmRestoreSubmission,
  declineRestoreSubmission,
  handleRestoreDialogOpen,
  submitSolution,
  sendReviewChat,
  openReviewChat,
  toggleHints,
  goNavigator,
  goTrack,
  logout,
} = useArenaPage()
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
          <button class="workspace-nav-link" type="button" @click="goNavigator">Navegador</button>
          <button class="workspace-nav-link workspace-nav-link--active" type="button">Arena</button>
          <button v-if="routeTrackSlug" class="workspace-nav-link" type="button" @click="goTrack">
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
        @select-exercise="selectExercise"
        @open-history="openSubmissionSession"
        @go-track="goTrack"
        @go-navigator="goNavigator"
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
              :family-key="activeSessionConfig?.family_key ?? 'code_lab'"
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
                  :session-config="activeSessionConfig"
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
                  @go-navigator="goNavigator"
                  @go-track="goTrack"
                />
              </div>

              <div class="right-column">
                <ArenaSurfaceHost
                  v-model:code="code"
                  v-model:selected-options="selectedOptions"
                  v-model:response-text="responseText"
                  :surface-key="activeSessionConfig?.surface_key ?? 'code_editor_single'"
                  :read-only="submissionFlow.isSubmitting.value"
                  :exercise-title="activeExercise?.title ?? 'atividade'"
                  :session-config="activeSessionConfig"
                />
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
      :family-key="activeSessionConfig?.family_key ?? 'code_lab'"
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
          <DialogTitle>Restaurar última tentativa?</DialogTitle>
          <DialogDescription>
            Encontramos uma sessão anterior sua para
            <strong>{{ pendingRestoreSubmission?.exercise_title ?? activeExercise?.title ?? 'este exercício' }}</strong>.
          </DialogDescription>
        </DialogHeader>
        <div class="hint-content">
          <div class="hint-block">
            <p class="section-label">Escolha como abrir</p>
            <p>Você pode continuar da sua última tentativa salva ou começar com o editor totalmente em branco.</p>
          </div>
          <label class="remember-choice-row">
            <input v-model="rememberRestoreChoice" type="checkbox" />
            <span>Lembrar minha resposta</span>
          </label>
        </div>
        <div class="arena-confirm-dialog__actions">
          <Button variant="outline" @click="declineRestoreSubmission">Começar em branco</Button>
          <Button @click="confirmRestoreSubmission">Abrir última tentativa</Button>
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
