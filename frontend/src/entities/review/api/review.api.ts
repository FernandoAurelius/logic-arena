import { apiClients, buildAuthHeaders } from '@/shared/api'

import type { AIReview, ReviewChatInput, ReviewChatMessage, ReviewChatResponse } from '../model/types'
import type { EvaluationRun } from '@/entities/evaluation'

export const reviewApi = {
  async getEvaluationReview(evaluationRunId: number, authorization?: string): Promise<AIReview> {
    return apiClients.review.get('/api/review/evaluations/:evaluation_run_id/review', {
      params: { evaluation_run_id: evaluationRunId },
      headers: buildAuthHeaders(authorization),
    }) as Promise<AIReview>
  },

  async getEvaluation(evaluationRunId: number, authorization?: string): Promise<EvaluationRun> {
    return apiClients.review.get('/api/review/evaluations/:evaluation_run_id', {
      params: { evaluation_run_id: evaluationRunId },
      headers: buildAuthHeaders(authorization),
    }) as Promise<EvaluationRun>
  },

  async sendChat(
    evaluationRunId: number,
    message: string,
    history: ReviewChatMessage[],
    authorization?: string,
  ): Promise<ReviewChatResponse> {
    const payload: ReviewChatInput = { message, history }
    return apiClients.review.post(
      '/api/review/evaluations/:evaluation_run_id/chat',
      payload,
      {
        params: { evaluation_run_id: evaluationRunId },
        headers: buildAuthHeaders(authorization),
      },
    ) as Promise<ReviewChatResponse>
  },
}
