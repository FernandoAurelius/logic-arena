import type { infer as ZodInfer } from 'zod'

import { apiClients, schemas } from '@/shared/api'

type ExerciseSummary = ZodInfer<typeof schemas.ExerciseSummarySchema>
type ExerciseDetail = ZodInfer<typeof schemas.ExerciseDetailSchema>

export const exerciseApi = {
  async list(authorization?: string): Promise<ExerciseSummary[]> {
    return apiClients.practice.get('/api/practice/exercises', {
      headers: { authorization: authorization ?? undefined },
    }) as Promise<ExerciseSummary[]>
  },
  async getBySlug(slug: string, authorization?: string): Promise<ExerciseDetail> {
    return apiClients.practice.get('/api/practice/exercises/:slug', {
      params: { slug },
      headers: { authorization: authorization ?? undefined },
    }) as Promise<ExerciseDetail>
  },
}
