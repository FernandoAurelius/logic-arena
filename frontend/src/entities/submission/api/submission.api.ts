import type {
  FeedbackPayload,
  AttemptEvaluationResponse,
  AttemptSession,
  ReviewChatMessage,
  SessionConfig,
  Submission,
  SubmissionSummary,
} from '@/entities/submission/model/types'
import { practiceSessionApi } from '@/entities/practice-session'
import { reviewApi } from '@/entities/review'

function mapVerdictToStatus(verdict?: string | null) {
  switch (verdict) {
    case 'passed':
      return 'passed'
    case 'failed':
      return 'failed'
    case 'error':
      return 'error'
    case 'partial':
      return 'failed'
    default:
      return 'pending'
  }
}

function mapReviewToFeedbackPayload(session: AttemptSession): FeedbackPayload | null {
  const review = session.latest_review
  if (!review) return null
  return {
    summary: review.explanation ?? '',
    strengths: [],
    issues: [],
    next_steps: review.next_steps ?? [],
    source: review.profile_key ?? 'review',
  }
}

function deriveEvaluationCounts(session: AttemptSession) {
  const evaluation = session.latest_evaluation
  const rawPassed = Number(evaluation?.evaluator_results?.passed_tests)
  const rawTotal = Number(evaluation?.evaluator_results?.total_tests)

  if (Number.isFinite(rawPassed) && Number.isFinite(rawTotal) && rawTotal > 0) {
    return {
      passed_tests: rawPassed,
      total_tests: rawTotal,
    }
  }

  const isObjectiveEvaluation =
    session.family_key === 'objective_item'
    || evaluation?.evaluator_results?.family_key === 'objective_item'

  if (isObjectiveEvaluation && evaluation) {
    return {
      passed_tests: evaluation.evaluator_results?.passed ? 1 : 0,
      total_tests: 1,
    }
  }

  return {
    passed_tests: 0,
    total_tests: 0,
  }
}

function mapEvaluationResults(session: AttemptSession) {
  const evaluation = session.latest_evaluation
  const familyKey = session.family_key ?? evaluation?.evaluator_results?.family_key
  const rawResults = Array.isArray(evaluation?.evidence_bundle?.results) ? evaluation?.evidence_bundle?.results : []

  if (familyKey === 'contract_behavior_lab') {
    return rawResults.map((result: any, index: number) => ({
      index: index + 1,
      input_data: result.check ?? 'check',
      expected_output: typeof result.expected === 'string' ? result.expected : JSON.stringify(result.expected ?? null),
      actual_output: typeof result.actual === 'string' ? result.actual : JSON.stringify(result.actual ?? null),
      passed: Boolean(result.passed),
      stderr: result.detail ?? '',
    }))
  }

  return rawResults as any[]
}

function mapSessionToSubmissionSummary(session: AttemptSession): SubmissionSummary {
  const evaluation = session.latest_evaluation
  const review = session.latest_review
  const evaluationCounts = deriveEvaluationCounts(session)
  return {
    id: session.id,
    exercise_slug: session.exercise_slug ?? '',
    exercise_title: session.exercise_title ?? session.exercise_slug ?? 'Exercício',
    status: mapVerdictToStatus(evaluation?.verdict),
    passed_tests: evaluationCounts.passed_tests,
    total_tests: evaluationCounts.total_tests,
    feedback_status: review ? (review.explanation === 'Revisão com IA em processamento...' ? 'pending' : 'ready') : 'pending',
    feedback_source: review?.profile_key ?? 'review',
    created_at: session.updated_at,
    evaluation_run_id: evaluation?.id ?? null,
  }
}

function mapSessionToSubmission(session: AttemptSession): Submission {
  const evaluation = session.latest_evaluation
  const review = session.latest_review
  const feedbackPayload = mapReviewToFeedbackPayload(session)
  const evaluationCounts = deriveEvaluationCounts(session)
  const snapshotFiles =
    session.latest_snapshot?.files && typeof session.latest_snapshot.files === 'object'
      ? Object.fromEntries(
          Object.entries(session.latest_snapshot.files as Record<string, unknown>).map(([fileName, value]) => [
            fileName,
            typeof value === 'object' && value !== null && 'content' in value
              ? String((value as Record<string, unknown>).content ?? '')
              : String(value ?? ''),
          ]),
        )
      : {}
  const answerFiles =
    session.answer_state?.files && typeof session.answer_state.files === 'object'
      ? Object.fromEntries(
          Object.entries(session.answer_state.files as Record<string, unknown>).map(([fileName, value]) => [
            fileName,
            String(value ?? ''),
          ]),
        )
      : {}
  const workspaceFiles =
    session.current_workspace_state?.files && typeof session.current_workspace_state.files === 'object'
      ? Object.fromEntries(
          Object.entries(session.current_workspace_state.files as Record<string, unknown>).map(([fileName, value]) => [
            fileName,
            typeof value === 'object' && value !== null && 'content' in value
              ? String((value as Record<string, unknown>).content ?? '')
              : String(value ?? ''),
          ]),
        )
      : {}
  const files = Object.keys(answerFiles).length > 0
    ? answerFiles
    : Object.keys(snapshotFiles).length > 0
      ? snapshotFiles
      : workspaceFiles
  return {
    id: session.id,
    session_id: session.id,
    evaluation_run_id: evaluation?.id ?? null,
    exercise_slug: session.exercise_slug ?? null,
    exercise_title: session.exercise_title ?? null,
    status: mapVerdictToStatus(evaluation?.verdict),
    passed_tests: evaluationCounts.passed_tests,
    total_tests: evaluationCounts.total_tests,
    source_code: String(
      session.answer_state?.source_code
      ?? session.latest_snapshot?.payload?.source_code
      ?? '',
    ),
    files,
    entrypoint: String(
      session.answer_state?.entrypoint
      ?? session.latest_snapshot?.payload?.entrypoint
      ?? session.current_workspace_state?.entrypoint
      ?? '',
    ) || null,
    active_file: String(
      session.answer_state?.active_file
      ?? session.current_workspace_state?.active_file
      ?? '',
    ) || null,
    selected_options: Array.isArray(session.answer_state?.selected_options)
      ? (session.answer_state.selected_options as string[])
      : Array.isArray(session.latest_snapshot?.selected_options)
        ? (session.latest_snapshot.selected_options as string[])
        : [],
    response_text: String(
      session.answer_state?.response_text
      ?? session.latest_snapshot?.payload?.response_text
      ?? '',
    ),
    console_output: String(evaluation?.evidence_bundle?.console_output ?? ''),
    feedback: feedbackPayload?.summary ?? '',
    feedback_status: review ? (review.explanation === 'Revisão com IA em processamento...' ? 'pending' : 'ready') : 'pending',
    feedback_source: review?.profile_key ?? 'review',
    feedback_payload: feedbackPayload,
    review_chat_history: (review?.conversation_thread as ReviewChatMessage[] | undefined) ?? [],
    created_at: session.latest_snapshot?.created_at ?? session.created_at,
    results: mapEvaluationResults(session),
    xp_awarded: session.xp_awarded ?? 0,
    unlocked_progress_rewards: session.unlocked_progress_rewards ?? [],
    exercise_progress: session.exercise_progress ?? null,
    user_progress: session.user_progress ?? null,
  }
}

function mapEvaluationResponseToSubmission(response: AttemptEvaluationResponse): Submission {
  const session = {
    ...response.session,
    latest_snapshot: response.snapshot,
    latest_evaluation: response.evaluation,
    latest_review: response.review ?? response.session.latest_review ?? null,
    xp_awarded: response.xp_awarded ?? response.session.xp_awarded ?? 0,
    unlocked_progress_rewards: response.unlocked_progress_rewards ?? response.session.unlocked_progress_rewards ?? [],
    exercise_progress: response.exercise_progress ?? response.session.exercise_progress ?? null,
    user_progress: response.user_progress ?? response.session.user_progress ?? null,
  }
  return mapSessionToSubmission(session)
}

export const submissionApi = {
  async listMine(authorization?: string): Promise<SubmissionSummary[]> {
    const sessions = await practiceSessionApi.listMine(authorization)
    return sessions.map(mapSessionToSubmissionSummary)
  },
  async getById(sessionId: number, authorization?: string): Promise<Submission> {
    const session = await practiceSessionApi.getById(sessionId, authorization)
    return mapSessionToSubmission(session)
  },
  async getSessionConfig(exerciseSlug: string, authorization?: string): Promise<SessionConfig> {
    return practiceSessionApi.getSessionConfig(exerciseSlug, authorization)
  },
  async openExerciseSession(exerciseSlug: string, authorization?: string): Promise<AttemptSession> {
    return practiceSessionApi.openExerciseSession(exerciseSlug, authorization)
  },
  async submit(
    sessionId: number,
    payload: {
      source_code?: string
      selected_options?: string[]
      response_text?: string
      files?: Record<string, unknown>
    },
    authorization?: string,
  ): Promise<Submission> {
    const response = await practiceSessionApi.submit(
      sessionId,
      {
        source_code: payload.source_code ?? '',
        selected_options: payload.selected_options ?? [],
        response_text: payload.response_text ?? '',
        files: payload.files ?? {},
      },
      authorization,
    )
    return mapEvaluationResponseToSubmission(response)
  },
  async sendReviewChat(
    evaluationRunId: number,
    message: string,
    history: ReviewChatMessage[],
    authorization?: string,
  ): Promise<{ answer: string }> {
    return reviewApi.sendChat(evaluationRunId, message, history, authorization)
  },
}
