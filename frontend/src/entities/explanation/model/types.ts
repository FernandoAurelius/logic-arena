import type { infer as ZodInfer } from 'zod'

import { schemas } from '@/shared/api'

export type ExerciseExplanation = ZodInfer<typeof schemas.ExerciseExplanationSchema>
