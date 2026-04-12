import type { infer as ZodInfer } from 'zod'

import { schemas } from '@/shared/api/generated'
import { apiClients } from '@/shared/api/zodios'

type ExerciseSummary = ZodInfer<typeof schemas.ExerciseSummarySchema>
type ExerciseDetail = ZodInfer<typeof schemas.ExerciseDetailSchema>

export const exerciseApi = {
  async list(authorization?: string): Promise<ExerciseSummary[]> {
    return apiClients.exercises.get('/api/exercises/', {
      headers: { authorization: authorization ?? undefined },
    }) as Promise<ExerciseSummary[]>
  },
  async getBySlug(slug: string, authorization?: string): Promise<ExerciseDetail> {
    return apiClients.exercises.get('/api/exercises/:slug', {
      params: { slug },
      headers: { authorization: authorization ?? undefined },
    }) as Promise<ExerciseDetail>
  },
}
