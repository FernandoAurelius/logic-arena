import type { infer as ZodInfer } from 'zod'

import { schemas } from '@/shared/api/generated'

export type TrackDetail = ZodInfer<typeof schemas.TrackDetailSchema>
export type TrackExercise = ZodInfer<typeof schemas.TrackExerciseSchema>
