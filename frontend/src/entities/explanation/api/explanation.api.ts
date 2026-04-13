import type { ExerciseExplanation } from '@/entities/explanation'
import { apiClients, buildAuthHeaders } from '@/shared/api'

export const explanationApi = {
  async getByTrackAndExercise(trackSlug: string, exerciseSlug: string, authorization?: string): Promise<ExerciseExplanation> {
    return apiClients.catalog.get('/api/catalog/tracks/:track_slug/explanations/:exercise_slug', {
      params: {
        track_slug: trackSlug,
        exercise_slug: exerciseSlug,
      },
      headers: buildAuthHeaders(authorization),
    }) as Promise<ExerciseExplanation>
  },
}
