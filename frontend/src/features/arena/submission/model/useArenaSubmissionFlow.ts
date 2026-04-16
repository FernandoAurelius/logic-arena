import { computed, ref } from 'vue'
import type { Ref } from 'vue'

import { submissionApi, type ProgressReward, type ReviewChatMessage, type Submission } from '@/entities/submission'
import type { SessionConfig } from '@/entities/practice-session'

type ResultsTab = 'saida' | 'testes' | 'revisao' | 'chat'

type UseArenaSubmissionFlowOptions = {
  authHeader: () => string | null
  activeSessionId: Ref<number | null>
  activeSessionConfig: Ref<SessionConfig | null>
  code: Ref<string>
  workspaceFiles: Ref<Record<string, string>>
  activeFile: Ref<string>
  selectedOptions: Ref<string[]>
  responseText: Ref<string>
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
    if (!submission) return 'Execute uma tentativa para receber o diagnóstico desta rodada.'
    const familyKey = options.activeSessionConfig.value?.family_key
    if (submission.status === 'passed' && submission.xp_awarded > 0) {
      return 'Você concluiu o exercício e desbloqueou um marco real de progresso.'
    }
    if (submission.status === 'passed') {
      return 'A solução está correta, mas esta rodada não mudou seu estado estrutural de progresso.'
    }
    if (familyKey === 'restricted_code') {
      return 'A correção ainda precisa de ajuste estrutural. Use a revisão para focar nos critérios que falharam.'
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

  async function refreshSubmission(sessionId: number) {
    const refreshed = await submissionApi.getById(sessionId, options.authHeader() ?? undefined)
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

  function startFeedbackPolling(sessionId: number) {
    stopFeedbackPolling()
    feedbackPollTimer.value = window.setInterval(() => {
      void refreshSubmission(sessionId).catch((error) => {
        console.error(error)
        stopFeedbackPolling()
      })
    }, 1500)
  }

  async function submitSolution() {
    if (!options.activeSessionId.value) return false

    isSubmitting.value = true
    resultsDialogOpen.value = false
    options.chatMessages.value = []

    try {
      const normalizedFiles = {
        ...options.workspaceFiles.value,
      }
      if (options.activeFile.value) {
        normalizedFiles[options.activeFile.value] = options.code.value
      }
      const entrypoint = String(
        options.activeSessionConfig.value?.workspace_spec?.entrypoint
        ?? options.latestSubmission.value?.entrypoint
        ?? options.activeFile.value
        ?? '',
      )
      const canonicalSourceCode = entrypoint
        ? (normalizedFiles[entrypoint] ?? options.code.value)
        : options.code.value
      const payload = {
        source_code: canonicalSourceCode,
        selected_options: [...options.selectedOptions.value],
        response_text: options.responseText.value,
        files: normalizedFiles,
      }
      const submission = await submissionApi.submit(
        options.activeSessionId.value,
        payload,
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
    if (!submission || !chatInput.value.trim() || !submission.evaluation_run_id) return

    const message = chatInput.value.trim()
    options.chatMessages.value.push({ role: 'user', content: message })
    chatInput.value = ''
    isChatBusy.value = true

    try {
      const response = await submissionApi.sendReviewChat(
        submission.evaluation_run_id,
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
      const familyKey = options.activeSessionConfig.value?.family_key
      const completionUnit = familyKey === 'restricted_code'
        ? (submission.total_tests === 1 ? 'critério estrutural' : 'critérios estruturais')
        : (submission.total_tests === 1 ? 'critério' : 'critérios')
      options.chatMessages.value = [
        {
          role: 'assistant',
          content: `Vamos revisar essa tentativa. Você passou ${submission.passed_tests} de ${submission.total_tests} ${completionUnit}. Me pergunte sobre um erro específico, uma melhoria de código ou o raciocínio esperado.`,
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
