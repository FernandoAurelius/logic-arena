import { computed, ref } from 'vue'
import type { Ref } from 'vue'
import type { infer as ZodInfer } from 'zod'

import { schemas } from '@/shared/api'
import { submissionApi } from '@/entities/submission/api/submission.api'

type Submission = ZodInfer<typeof schemas.SubmissionSchema>
type ReviewChatMessage = ZodInfer<typeof schemas.ReviewChatMessageSchema>
type ProgressReward = ZodInfer<typeof schemas.ProgressRewardSchema>

type ResultsTab = 'saida' | 'testes' | 'revisao' | 'chat'

type UseArenaSubmissionFlowOptions = {
  authHeader: () => string | null
  activeExerciseSlug: Ref<string | null>
  code: Ref<string>
  latestSubmission: Ref<Submission | null>
  chatMessages: Ref<ReviewChatMessage[]>
  onSubmissionHydrated: (submission: Submission) => void
  onSubmissionProgress: (submission: Submission) => void
  onSubmissionPassed?: (submission: Submission) => void
  onReloadSubmissions: () => Promise<void>
}

export function useArenaSubmissionFlow(options: UseArenaSubmissionFlowOptions) {
  const isSubmitting = ref(false)
  const isChatBusy = ref(false)
  const resultsDialogOpen = ref(false)
  const resultsTab = ref<ResultsTab>('saida')
  const feedbackPollTimer = ref<number | null>(null)

  const consoleLines = computed(() => {
    if (!options.latestSubmission.value?.console_output) return ['[INIT] Aguardando execução do módulo atual...']
    return options.latestSubmission.value.console_output.split('\n').filter(Boolean)
  })
  const feedbackPayload = computed(() => options.latestSubmission.value?.feedback_payload ?? null)
  const isFeedbackPending = computed(() => options.latestSubmission.value?.feedback_status === 'pending')
  const canReviewWithAi = computed(() => Boolean(options.latestSubmission.value) && !isFeedbackPending.value)
  const progressRewards = computed<ProgressReward[]>(() => options.latestSubmission.value?.unlocked_progress_rewards ?? [])
  const submissionOutcomeTone = computed(() => {
    const submission = options.latestSubmission.value
    if (!submission) return 'idle'
    if (submission.status === 'passed' && submission.xp_awarded > 0) return 'reward'
    if (submission.status === 'passed') return 'pass'
    return 'fail'
  })
  const submissionOutcomeTitle = computed(() => {
    const submission = options.latestSubmission.value
    if (!submission) return 'Aguardando execução'
    if (submission.status === 'passed' && submission.xp_awarded > 0) return 'Passou e evoluiu'
    if (submission.status === 'passed') return 'Passou, mas sem novo XP'
    return 'Ainda não passou'
  })
  const submissionOutcomeCopy = computed(() => {
    const submission = options.latestSubmission.value
    if (!submission) return 'Execute um exercício para receber o diagnóstico desta rodada.'
    if (submission.status === 'passed' && submission.xp_awarded > 0) {
      return 'Você concluiu o exercício e desbloqueou um marco real de progresso.'
    }
    if (submission.status === 'passed') {
      return 'A solução está correta, mas esta rodada não mudou seu estado estrutural de progresso.'
    }
    return 'A rodada ainda precisa de ajuste. Use o console e a revisão com IA para entender onde corrigir.'
  })
  const rewardSummary = computed(() => {
    const submission = options.latestSubmission.value
    if (!submission) return ''
    if (submission.xp_awarded > 0 && progressRewards.value.length > 0) {
      return `${progressRewards.value.map((reward) => reward.label).join(', ')}: +${submission.xp_awarded} XP`
    }
    if (submission.xp_awarded > 0) {
      return `+${submission.xp_awarded} XP nesta rodada`
    }
    return 'Sem ganho de XP nesta rodada'
  })

  function stopFeedbackPolling() {
    if (feedbackPollTimer.value !== null) {
      window.clearInterval(feedbackPollTimer.value)
      feedbackPollTimer.value = null
    }
  }

  function openResultsCenter(tab: ResultsTab = 'saida') {
    resultsTab.value = tab
    resultsDialogOpen.value = true
  }

  async function refreshSubmission(submissionId: number) {
    const refreshed = await submissionApi.getById(submissionId, options.authHeader() ?? undefined)
    options.latestSubmission.value = {
      ...refreshed,
      results: refreshed.results.length ? refreshed.results : options.latestSubmission.value?.results ?? [],
    }
    options.onSubmissionProgress(refreshed)
    if ((refreshed.review_chat_history?.length ?? 0) > 0) {
      options.chatMessages.value = refreshed.review_chat_history
    }
    if (refreshed.feedback_status !== 'pending') {
      stopFeedbackPolling()
      await options.onReloadSubmissions()
      if (refreshed.status === 'passed') {
        options.onSubmissionPassed?.(refreshed)
      }
    }
  }

  function startFeedbackPolling(submissionId: number) {
    stopFeedbackPolling()
    feedbackPollTimer.value = window.setInterval(() => {
      void refreshSubmission(submissionId).catch((error) => {
        console.error(error)
        stopFeedbackPolling()
      })
    }, 1500)
  }

  async function submitSolution() {
    if (!options.activeExerciseSlug.value) return false

    isSubmitting.value = true
    resultsDialogOpen.value = false
    options.chatMessages.value = []

    try {
      const submission = await submissionApi.submit(
        options.activeExerciseSlug.value,
        options.code.value,
        options.authHeader() ?? undefined,
      )
      options.onSubmissionHydrated(submission)
      options.onSubmissionProgress(submission)
      await options.onReloadSubmissions()
      if (submission.status === 'passed') {
        options.onSubmissionPassed?.(submission)
      }
      openResultsCenter('saida')
      return true
    } finally {
      isSubmitting.value = false
    }
  }

  async function sendReviewChat(chatInput: Ref<string>) {
    const submission = options.latestSubmission.value
    if (!submission || !chatInput.value.trim()) return

    const message = chatInput.value.trim()
    options.chatMessages.value.push({ role: 'user', content: message })
    chatInput.value = ''
    isChatBusy.value = true

    try {
      const response = await submissionApi.sendReviewChat(
        submission.id,
        message,
        options.chatMessages.value,
        options.authHeader() ?? undefined,
      )
      options.chatMessages.value.push({ role: 'assistant', content: response.answer })
      if (options.latestSubmission.value) {
        options.latestSubmission.value.review_chat_history = [...options.chatMessages.value]
      }
    } catch (error) {
      console.error(error)
      options.chatMessages.value.push({
        role: 'assistant',
        content: 'Não consegui revisar essa dúvida agora. Tente novamente em instantes.',
      })
    } finally {
      isChatBusy.value = false
    }
  }

  function openReviewChat() {
    const submission = options.latestSubmission.value
    if (!submission) return
    if (options.chatMessages.value.length === 0) {
      options.chatMessages.value = [
        {
          role: 'assistant',
          content: `Vamos revisar essa submissão. Você passou ${submission.passed_tests} de ${submission.total_tests} testes. Me pergunte sobre um erro específico, uma melhoria de código ou o raciocínio esperado.`,
        },
      ]
    }
    openResultsCenter('chat')
  }

  return {
    isSubmitting,
    isChatBusy,
    resultsDialogOpen,
    resultsTab,
    consoleLines,
    feedbackPayload,
    isFeedbackPending,
    canReviewWithAi,
    progressRewards,
    submissionOutcomeTone,
    submissionOutcomeTitle,
    submissionOutcomeCopy,
    rewardSummary,
    openResultsCenter,
    submitSolution,
    sendReviewChat,
    openReviewChat,
    startFeedbackPolling,
    stopFeedbackPolling,
  }
}
