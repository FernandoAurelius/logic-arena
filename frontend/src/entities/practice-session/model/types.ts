import type { infer as ZodInfer } from 'zod'

import { schemas } from '@/shared/api'

export type AttemptSession = ZodInfer<typeof schemas.AttemptSessionSchema>
export type PracticeSession = AttemptSession

export type SessionConfig = ZodInfer<typeof schemas.SessionConfigSchema>
export type PracticeAnswerInput = ZodInfer<typeof schemas.PracticeAnswerInputSchema>

export type AttemptEvaluationResponse = ZodInfer<typeof schemas.AttemptEvaluationResponseSchema>
export type PracticeEvaluationResponse = AttemptEvaluationResponse

export type SubmissionSnapshot = ZodInfer<typeof schemas.SubmissionSnapshotSchema>
export type ProgressReward = ZodInfer<typeof schemas.ProgressRewardSchema>
export type ExerciseProgress = ZodInfer<typeof schemas.ExerciseProgressSchema>
export type UserProgressSummary = ZodInfer<typeof schemas.UserProgressSummarySchema>
