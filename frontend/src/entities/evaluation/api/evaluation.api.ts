import { apiClients, buildAuthHeaders } from '@/shared/api'

import type { EvaluationRun } from '../model/types'

export const evaluationApi = {
  async getById(evaluationRunId: number, authorization?: string): Promise<EvaluationRun> {
    return apiClients.review.get('/api/review/evaluations/:evaluation_run_id', {
      params: { evaluation_run_id: evaluationRunId },
      headers: buildAuthHeaders(authorization),
    }) as Promise<EvaluationRun>
  },
}
