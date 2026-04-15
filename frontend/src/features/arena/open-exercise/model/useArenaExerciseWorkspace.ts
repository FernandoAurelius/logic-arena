import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { catalogApi } from '@/entities/catalog/api/catalog.api'
import { exerciseApi, type ExerciseDetail, type ExerciseSummary } from '@/entities/exercise'
import { submissionApi, type ReviewChatMessage, type SessionConfig, type Submission, type SubmissionSummary } from '@/entities/submission'
import type { TrackDetail, TrackExercise } from '@/entities/track'

type ArenaExerciseWorkspaceOptions = {
  authHeader: () => string | null
  onSubmissionHydrated?: (submission: Submission) => void
  onStopFeedbackPolling?: () => void
  onStartFeedbackPolling?: (submissionId: number) => void
}

type GroupedExercise = {
  key: string
  label: string
  exercises: Array<ExerciseSummary | TrackExercise>
}

const RESTORE_CHOICE_STORAGE_KEY = 'logic-arena.restore-choice'
type RestoreChoice = 'restore' | 'blank'

export function useArenaExerciseWorkspace(options: ArenaExerciseWorkspaceOptions) {
  const route = useRoute()
  const router = useRouter()

  const exercises = ref<ExerciseSummary[]>([])
  const activeExercise = ref<ExerciseDetail | null>(null)
  const activeSessionId = ref<number | null>(null)
  const activeSessionConfig = ref<SessionConfig | null>(null)
  const submissions = ref<SubmissionSummary[]>([])
  const trackContext = ref<TrackDetail | null>(null)
  const code = ref('')
  const latestSubmission = ref<Submission | null>(null)
  const chatMessages = ref<ReviewChatMessage[]>([])
  const isBooting = ref(false)
  const errorMessage = ref('')
  const restoreDialogOpen = ref(false)
  const pendingRestoreSubmission = ref<SubmissionSummary | null>(null)
  const rememberRestoreChoice = ref(false)

  const routeTrackSlug = computed(() => (typeof route.query.track === 'string' ? route.query.track : null))
  const groupedExercises = computed<GroupedExercise[]>(() => {
    const source = routeTrackSlug.value && trackContext.value?.slug === routeTrackSlug.value
      ? trackContext.value.exercises
      : routeTrackSlug.value
        ? exercises.value.filter((exercise) => exercise.track_slug === routeTrackSlug.value)
        : exercises.value
    const groups = new Map<string, GroupedExercise>()
    for (const exercise of source) {
      const key = routeTrackSlug.value ? exercise.track_slug ?? 'trilha-livre' : exercise.module_slug ?? exercise.category_slug ?? 'sem-modulo'
      const label = routeTrackSlug.value ? exercise.track_name ?? 'Trilha livre' : exercise.module_name ?? exercise.category_name ?? 'Sem módulo'
      if (!groups.has(key)) {
        groups.set(key, { key, label, exercises: [] })
      }
      groups.get(key)?.exercises.push(exercise)
    }
    return Array.from(groups.values()).map((group) => ({
      ...group,
      exercises: group.exercises.slice().sort((left, right) => {
        const leftPosition = Number(('position' in left ? left.position : left.track_position) ?? 0)
        const rightPosition = Number(('position' in right ? right.position : right.track_position) ?? 0)
        if (routeTrackSlug.value && leftPosition !== rightPosition) {
          return leftPosition - rightPosition
        }
        return left.title.localeCompare(right.title)
      }),
    }))
  })
  const trackExercises = computed<TrackExercise[]>(() => {
    if (routeTrackSlug.value && trackContext.value?.slug === routeTrackSlug.value) {
      return trackContext.value.exercises
    }
    return []
  })
  const activeTrackIndex = computed(() => {
    if (!activeExercise.value || trackExercises.value.length === 0) return -1
    return trackExercises.value.findIndex((exercise) => exercise.slug === activeExercise.value?.slug)
  })
  const previousTrackExercise = computed(() => {
    const index = activeTrackIndex.value
    if (index <= 0) return null
    return trackExercises.value[index - 1]
  })
  const nextTrackExercise = computed(() => {
    const index = activeTrackIndex.value
    if (index < 0 || index >= trackExercises.value.length - 1) return null
    return trackExercises.value[index + 1]
  })
  const sidebarHistory = computed(() => submissions.value.slice(0, 6))

  function clearDraftForExercise() {
    options.onStopFeedbackPolling?.()
    latestSubmission.value = null
    code.value = ''
    chatMessages.value = []
  }

  function setHydratedSubmission(submission: Submission) {
    latestSubmission.value = submission
    activeSessionId.value = submission.session_id
    code.value = submission.source_code
    chatMessages.value = submission.review_chat_history ?? []
    if (submission.feedback_status === 'pending' && submission.session_id) {
      options.onStartFeedbackPolling?.(submission.session_id)
    } else {
      options.onStopFeedbackPolling?.()
    }
  }

  function findLatestSubmissionForExercise(slug: string) {
    return submissions.value.find((submission) => submission.exercise_slug === slug) ?? null
  }

  async function fetchExercise(slug: string) {
    return exerciseApi.getBySlug(slug, options.authHeader() ?? undefined)
  }

  async function fetchSessionConfig(slug: string) {
    return submissionApi.getSessionConfig(slug, options.authHeader() ?? undefined)
  }

  async function fetchSubmission(sessionId: number) {
    return submissionApi.getById(sessionId, options.authHeader() ?? undefined)
  }

  async function loadExercises() {
    exercises.value = await exerciseApi.list(options.authHeader() ?? undefined)
    const requestedSlug = typeof route.query.exercise === 'string' ? route.query.exercise : null
    const initialExercise = (requestedSlug && exercises.value.find((exercise) => exercise.slug === requestedSlug)) ?? exercises.value[0]
    if (!activeExercise.value && initialExercise) {
      await selectExercise(initialExercise.slug)
    }
  }

  async function loadTrackContext(trackSlug: string | null) {
    if (!trackSlug) {
      trackContext.value = null
      return
    }

    try {
      trackContext.value = await catalogApi.getTrackDetail(trackSlug, options.authHeader() ?? undefined)
    } catch (error) {
      console.error(error)
      trackContext.value = null
    }
  }

  async function loadSubmissions() {
    submissions.value = await submissionApi.listMine(options.authHeader() ?? undefined)
  }

  function promptRestoreLatestSubmissionForExercise(slug: string) {
    const submissionSummary = findLatestSubmissionForExercise(slug)
    if (!submissionSummary) {
      pendingRestoreSubmission.value = null
      restoreDialogOpen.value = false
      return false
    }

    const storedChoice = globalThis.localStorage?.getItem(RESTORE_CHOICE_STORAGE_KEY) as RestoreChoice | null
    if (storedChoice === 'restore') {
      void restoreSubmissionById(submissionSummary.id)
      return true
    }

    if (storedChoice === 'blank') {
      clearDraftForExercise()
      return true
    }

    rememberRestoreChoice.value = false
    pendingRestoreSubmission.value = submissionSummary
    restoreDialogOpen.value = true
    return true
  }

  async function restoreSubmissionById(submissionId: number) {
    const submission = await fetchSubmission(submissionId)
    setHydratedSubmission(submission)
    return true
  }

  async function confirmRestoreSubmission() {
    const submissionSummary = pendingRestoreSubmission.value
    restoreDialogOpen.value = false
    pendingRestoreSubmission.value = null
    if (rememberRestoreChoice.value) {
      globalThis.localStorage?.setItem(RESTORE_CHOICE_STORAGE_KEY, 'restore')
    }
    rememberRestoreChoice.value = false
    if (!submissionSummary) return
    await restoreSubmissionById(submissionSummary.id)
  }

  function declineRestoreSubmission() {
    restoreDialogOpen.value = false
    pendingRestoreSubmission.value = null
    if (rememberRestoreChoice.value) {
      globalThis.localStorage?.setItem(RESTORE_CHOICE_STORAGE_KEY, 'blank')
    }
    rememberRestoreChoice.value = false
    clearDraftForExercise()
  }

  function handleRestoreDialogOpen(nextOpen: boolean) {
    restoreDialogOpen.value = nextOpen
    if (!nextOpen) {
      pendingRestoreSubmission.value = null
      rememberRestoreChoice.value = false
    }
  }

  async function selectExercise(slug: string) {
    isBooting.value = true
    errorMessage.value = ''
    options.onStopFeedbackPolling?.()
    restoreDialogOpen.value = false
    pendingRestoreSubmission.value = null

    try {
      const [exercise, sessionConfig, initialSession] = await Promise.all([
        fetchExercise(slug),
        fetchSessionConfig(slug),
        submissionApi.openExerciseSession(slug, options.authHeader() ?? undefined),
      ])
      activeExercise.value = exercise
      activeSessionId.value = initialSession.id
      activeSessionConfig.value = sessionConfig
      clearDraftForExercise()
      code.value = String(initialSession.answer_state?.source_code ?? exercise.starter_code ?? '')
      if (route.query.exercise !== slug) {
        await router.replace({
          name: 'arena',
          query: {
            ...route.query,
            exercise: slug,
          },
        })
      }
      promptRestoreLatestSubmissionForExercise(slug)
    } catch (error) {
      console.error(error)
      errorMessage.value = 'Falha ao carregar os detalhes do exercício.'
    } finally {
      isBooting.value = false
    }
  }

  function navigateTrackExercise(direction: 'previous' | 'next') {
    const target = direction === 'previous' ? previousTrackExercise.value : nextTrackExercise.value
    if (!target) return
    void selectExercise(target.slug)
  }

  async function openSubmissionSession(submissionSummary: SubmissionSummary) {
    isBooting.value = true
    errorMessage.value = ''
    options.onStopFeedbackPolling?.()
    restoreDialogOpen.value = false
    pendingRestoreSubmission.value = null

    try {
      const [exercise, sessionConfig, submission] = await Promise.all([
        fetchExercise(submissionSummary.exercise_slug),
        fetchSessionConfig(submissionSummary.exercise_slug),
        fetchSubmission(submissionSummary.id),
      ])
      activeExercise.value = exercise
      activeSessionConfig.value = sessionConfig
      setHydratedSubmission(submission)
      options.onSubmissionHydrated?.(submission)
    } catch (error) {
      console.error(error)
      errorMessage.value = 'Não foi possível reabrir essa sessão do histórico.'
    } finally {
      isBooting.value = false
    }
  }

  async function bootstrapArena() {
    errorMessage.value = ''
    isBooting.value = true

    try {
      await Promise.all([loadTrackContext(routeTrackSlug.value), loadExercises(), loadSubmissions()])
    } catch (error) {
      console.error(error)
      errorMessage.value = 'Não foi possível carregar a arena autenticada.'
    } finally {
      isBooting.value = false
    }
  }

  return {
    exercises,
    activeExercise,
    activeSessionId,
    activeSessionConfig,
    submissions,
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
    fetchExercise,
    fetchSubmission,
    fetchSessionConfig,
    selectExercise,
    navigateTrackExercise,
    openSubmissionSession,
    clearDraftForExercise,
    setHydratedSubmission,
    confirmRestoreSubmission,
    declineRestoreSubmission,
    handleRestoreDialogOpen,
  }
}
