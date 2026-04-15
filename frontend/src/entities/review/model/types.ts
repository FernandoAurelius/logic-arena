import type { infer as ZodInfer } from 'zod'

import { schemas } from '@/shared/api'

export type ReviewChatMessage = ZodInfer<typeof schemas.ReviewChatMessageSchema>
export type AIReview = ZodInfer<typeof schemas.AIReviewSchema>
export type ReviewChatInput = ZodInfer<typeof schemas.ReviewChatInputSchema>
export type ReviewChatResponse = ZodInfer<typeof schemas.ReviewChatResponseSchema>
