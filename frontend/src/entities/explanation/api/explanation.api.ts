import type { infer as ZodInfer } from 'zod'

import { schemas } from '@/shared/api/generated'
import { apiClients } from '@/shared/api/zodios'

type ExerciseExplanation = ZodInfer<typeof schemas.ExerciseExplanationSchema>

export const explanationApi = {
  async getByTrackAndExercise(trackSlug: string, exerciseSlug: string, authorization?: string): Promise<ExerciseExplanation> {
    return apiClients.catalog.get('/api/catalog/tracks/:track_slug/explanations/:exercise_slug', {
      params: {
        track_slug: trackSlug,
        exercise_slug: exerciseSlug,
      },
      headers: { authorization: authorization ?? undefined },
    }) as Promise<ExerciseExplanation>
  },
}
