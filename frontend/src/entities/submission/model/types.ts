import type { infer as ZodInfer } from 'zod'

import { schemas } from '@/shared/api'

export type FeedbackPayload = ZodInfer<typeof schemas.FeedbackPayloadSchema>
export type ProgressReward = ZodInfer<typeof schemas.ProgressRewardSchema>
export type ReviewChatMessage = ZodInfer<typeof schemas.ReviewChatMessageSchema>
export type Submission = ZodInfer<typeof schemas.SubmissionSchema>
export type SubmissionSummary = ZodInfer<typeof schemas.SubmissionSummarySchema>
