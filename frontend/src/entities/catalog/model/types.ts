import type { infer as ZodInfer } from 'zod'

import { schemas } from '@/shared/api'

export type NavigatorResponse = ZodInfer<typeof schemas.NavigatorResponseSchema>
export type TrackSummary = ZodInfer<typeof schemas.TrackSummarySchema>
export type ModuleSummary = ZodInfer<typeof schemas.NavigatorModuleSchema>
