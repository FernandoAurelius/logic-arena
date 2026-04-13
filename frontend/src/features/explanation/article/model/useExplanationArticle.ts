import { ref } from 'vue'

import { explanationApi } from '@/entities/explanation/api/explanation.api'
import type { ExerciseExplanation } from '@/entities/explanation'

export function useExplanationArticle(authHeader: () => string | null) {
  const explanation = ref<ExerciseExplanation | null>(null)
  const loading = ref(false)
  const errorMessage = ref('')

  async function loadExplanation(trackSlug: string, exerciseSlug: string) {
    loading.value = true
    errorMessage.value = ''

    try {
      explanation.value = await explanationApi.getByTrackAndExercise(
        trackSlug,
        exerciseSlug,
        authHeader() ?? undefined,
      )
    } catch (error) {
      console.error(error)
      errorMessage.value = 'Não foi possível carregar a explanation deste módulo.'
    } finally {
      loading.value = false
    }
  }

  return {
    explanation,
    loading,
    errorMessage,
    loadExplanation,
  }
}
