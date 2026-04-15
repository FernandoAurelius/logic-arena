import { apiClients, buildAuthHeaders } from '@/shared/api'

import type {
  PracticeAnswerInput,
  AttemptEvaluationResponse,
  AttemptSession,
  SessionConfig,
} from '../model/types'

export const practiceSessionApi = {
  async listMine(authorization?: string): Promise<AttemptSession[]> {
    return apiClients.practice.get('/api/practice/sessions', {
      headers: buildAuthHeaders(authorization),
    }) as Promise<AttemptSession[]>
  },

  async getById(sessionId: number, authorization?: string): Promise<AttemptSession> {
    return apiClients.practice.get('/api/practice/sessions/:session_id', {
      params: { session_id: sessionId },
      headers: buildAuthHeaders(authorization),
    }) as Promise<AttemptSession>
  },

  async getSessionConfig(exerciseSlug: string, authorization?: string): Promise<SessionConfig> {
    return apiClients.practice.get('/api/practice/exercises/:slug/session-config', {
      params: { slug: exerciseSlug },
      headers: buildAuthHeaders(authorization),
    }) as Promise<SessionConfig>
  },

  async openExerciseSession(exerciseSlug: string, authorization?: string): Promise<AttemptSession> {
    return apiClients.practice.post(
      '/api/practice/exercises/:slug/sessions',
      {},
      {
        params: { slug: exerciseSlug },
        headers: buildAuthHeaders(authorization),
      },
    ) as Promise<AttemptSession>
  },

  async openAssessmentSession(assessmentSlug: string, authorization?: string): Promise<AttemptSession> {
    return apiClients.assessments.post(
      '/api/assessments/:slug/sessions',
      {},
      {
        params: { slug: assessmentSlug },
        headers: buildAuthHeaders(authorization),
      },
    ) as Promise<AttemptSession>
  },

  async run(sessionId: number, payload: PracticeAnswerInput, authorization?: string): Promise<AttemptEvaluationResponse> {
    return apiClients.practice.post(
      '/api/practice/sessions/:session_id/run',
      payload,
      {
        params: { session_id: sessionId },
        headers: buildAuthHeaders(authorization),
      },
    ) as Promise<AttemptEvaluationResponse>
  },

  async check(sessionId: number, payload: PracticeAnswerInput, authorization?: string): Promise<AttemptEvaluationResponse> {
    return apiClients.practice.post(
      '/api/practice/sessions/:session_id/check',
      payload,
      {
        params: { session_id: sessionId },
        headers: buildAuthHeaders(authorization),
      },
    ) as Promise<AttemptEvaluationResponse>
  },

  async submit(sessionId: number, payload: PracticeAnswerInput, authorization?: string): Promise<AttemptEvaluationResponse> {
    return apiClients.practice.post(
      '/api/practice/sessions/:session_id/submit',
      payload,
      {
        params: { session_id: sessionId },
        headers: buildAuthHeaders(authorization),
      },
    ) as Promise<AttemptEvaluationResponse>
  },

  async patchState(sessionId: number, payload: Record<string, unknown>, authorization?: string): Promise<AttemptSession> {
    return apiClients.practice.patch(
      '/api/practice/sessions/:session_id',
      payload,
      {
        params: { session_id: sessionId },
        headers: buildAuthHeaders(authorization),
      },
    ) as Promise<AttemptSession>
  },
}
