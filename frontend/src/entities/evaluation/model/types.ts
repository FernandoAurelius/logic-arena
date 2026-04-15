import type { infer as ZodInfer } from 'zod'

import { schemas } from '@/shared/api'

export type EvaluationRun = ZodInfer<typeof schemas.EvaluationRunSchema>
export type AttemptEvaluationResponse = ZodInfer<typeof schemas.AttemptEvaluationResponseSchema>
