import type { infer as ZodInfer } from 'zod'

import { schemas } from '@/shared/api'

export type ExerciseSummary = ZodInfer<typeof schemas.ExerciseSummarySchema>
export type ExerciseDetail = ZodInfer<typeof schemas.ExerciseDetailSchema>
