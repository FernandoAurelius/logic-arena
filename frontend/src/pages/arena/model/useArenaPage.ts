import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { useSession } from '@/entities/session'
import type { Submission, SubmissionSummary } from '@/entities/submission'
import { useArenaExerciseWorkspace } from '@/features/arena/open-exercise/model/useArenaExerciseWorkspace'
import { useArenaSubmissionFlow } from '@/features/arena/submission/model/useArenaSubmissionFlow'

export function useArenaPage() {
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

  function triggerLevelUp() {
    levelUpBurst.value = true
    if (levelUpTimer !== null) {
      window.clearTimeout(levelUpTimer)
    }
    levelUpTimer = window.setTimeout(() => {
      levelUpBurst.value = false
    }, 2600)
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

  function applySubmissionProgress(submission: Submission) {
    if (!submission.user_progress) return
    const previousLevel = session.currentUser.value?.level ?? 1
    session.mergeCurrentUserProgress(submission.user_progress)
    if (submission.user_progress.level > previousLevel) {
      triggerLevelUp()
      triggerConfetti()
    }
  }

  const workspace = useArenaExerciseWorkspace({
    authHeader: () => session.authHeader(),
    onSubmissionHydrated: applySubmissionProgress,
    onStopFeedbackPolling: () => submissionFlowRef?.stopFeedbackPolling(),
    onStartFeedbackPolling: (submissionId) => submissionFlowRef?.startFeedbackPolling(submissionId),
  })

  const submissionFlow = useArenaSubmissionFlow({
    authHeader: () => session.authHeader(),
    activeSessionId: workspace.activeSessionId,
    code: workspace.code,
    latestSubmission: workspace.latestSubmission,
    chatMessages: workspace.chatMessages,
    onSubmissionHydrated: workspace.setHydratedSubmission,
    onSubmissionProgress: applySubmissionProgress,
    onSubmissionPassed: () => triggerConfetti(),
    onReloadSubmissions: workspace.loadSubmissions,
  })
  submissionFlowRef = submissionFlow

  const activeIndex = computed(() => {
    if (!workspace.activeExercise.value) return 0
    return workspace.exercises.value.findIndex((exercise) => exercise.slug === workspace.activeExercise.value?.slug) + 1
  })
  const visibleTestCases = computed(() => workspace.activeExercise.value?.test_cases ?? [])
  const level = computed(() => session.currentUser.value?.level ?? 1)
  const xpIntoLevel = computed(() => session.currentUser.value?.xp_into_level ?? 0)
  const xpProgress = computed(() => Math.min(100, Math.max(0, xpIntoLevel.value)))
  const xpToNextLevel = computed(() => session.currentUser.value?.xp_to_next_level ?? 100)

  function resetArenaPanels() {
    submissionFlow.resultsDialogOpen.value = false
    hintsOpen.value = false
  }

  async function handleSelectExercise(slug: string) {
    resetArenaPanels()
    await workspace.selectExercise(slug)
  }

  function navigateTrackExercise(direction: 'previous' | 'next') {
    resetArenaPanels()
    workspace.navigateTrackExercise(direction)
  }

  async function handleOpenSubmissionSession(submissionSummary: SubmissionSummary) {
    resetArenaPanels()
    await workspace.openSubmissionSession(submissionSummary)
  }

  async function confirmRestoreSubmission() {
    await workspace.confirmRestoreSubmission()
    submissionFlow.resultsDialogOpen.value = false
  }

  function declineRestoreSubmission() {
    workspace.declineRestoreSubmission()
    submissionFlow.resultsDialogOpen.value = false
  }

  function handleRestoreDialogOpen(nextOpen: boolean) {
    workspace.handleRestoreDialogOpen(nextOpen)
  }

  async function submitSolution() {
    if (!workspace.activeExercise.value || !session.token.value) {
      workspace.errorMessage.value = 'Faça login antes de submeter uma solução.'
      return
    }

    workspace.errorMessage.value = ''

    try {
      workspace.pendingRestoreSubmission.value = null
      workspace.restoreDialogOpen.value = false
      await submissionFlow.submitSolution()
    } catch (error) {
      console.error(error)
      workspace.errorMessage.value = 'Não foi possível processar a tentativa.'
    }
  }

  async function sendReviewChat() {
    await submissionFlow.sendReviewChat(chatInput)
  }

  function openReviewChat() {
    submissionFlow.openReviewChat()
  }

  function toggleHints() {
    hintsOpen.value = !hintsOpen.value
  }

  function goNavigator() {
    void router.push({ name: 'navigator' })
  }

  function goTrack() {
    if (!workspace.routeTrackSlug.value) return
    void router.push({ name: 'track', params: { trackSlug: workspace.routeTrackSlug.value } })
  }

  async function logout() {
    submissionFlow.stopFeedbackPolling()
    session.clearSession()
    await router.push({ name: 'landing' })
  }

  watch(
    () => route.query.track,
    (trackSlug) => {
      void workspace.loadTrackContext(typeof trackSlug === 'string' ? trackSlug : null)
    },
  )

  watch(
    () => route.query.exercise,
    (exerciseSlug) => {
      if (typeof exerciseSlug !== 'string' || !exerciseSlug || workspace.activeExercise.value?.slug === exerciseSlug) {
        return
      }
      if (workspace.exercises.value.some((exercise) => exercise.slug === exerciseSlug)) {
        void handleSelectExercise(exerciseSlug)
      }
    },
  )

  onMounted(() => {
    void workspace.bootstrapArena()
  })

  onBeforeUnmount(() => {
    submissionFlow.stopFeedbackPolling()
    if (levelUpTimer !== null) {
      window.clearTimeout(levelUpTimer)
    }
  })

  return {
    session,
    hintsOpen,
    chatInput,
    confettiBurst,
    levelUpBurst,
    showProfile,
    specTab,
    routeTrackSlug: workspace.routeTrackSlug,
    exercises: workspace.exercises,
    activeExercise: workspace.activeExercise,
    activeSessionConfig: workspace.activeSessionConfig,
    trackContext: workspace.trackContext,
    code: workspace.code,
    latestSubmission: workspace.latestSubmission,
    chatMessages: workspace.chatMessages,
    isBooting: workspace.isBooting,
    errorMessage: workspace.errorMessage,
    restoreDialogOpen: workspace.restoreDialogOpen,
    pendingRestoreSubmission: workspace.pendingRestoreSubmission,
    rememberRestoreChoice: workspace.rememberRestoreChoice,
    groupedExercises: workspace.groupedExercises,
    trackExercises: workspace.trackExercises,
    activeTrackIndex: workspace.activeTrackIndex,
    previousTrackExercise: workspace.previousTrackExercise,
    nextTrackExercise: workspace.nextTrackExercise,
    sidebarHistory: workspace.sidebarHistory,
    activeIndex,
    visibleTestCases,
    level,
    xpIntoLevel,
    xpProgress,
    xpToNextLevel,
    submissionFlow,
    selectExercise: handleSelectExercise,
    navigateTrackExercise,
    openSubmissionSession: handleOpenSubmissionSession,
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
  }
}
