import type { infer as ZodInfer } from 'zod'

import { schemas } from '@/shared/api'
import { apiClients } from '@/shared/api/zodios'

type ReviewChatMessage = ZodInfer<typeof schemas.ReviewChatMessageSchema>
type Submission = ZodInfer<typeof schemas.SubmissionSchema>
type SubmissionSummary = ZodInfer<typeof schemas.SubmissionSummarySchema>

export const submissionApi = {
  async listMine(authorization?: string): Promise<SubmissionSummary[]> {
    return apiClients.submissions.get('/api/submissions/me', {
      headers: { authorization: authorization ?? undefined },
    }) as Promise<SubmissionSummary[]>
  },
  async getById(submissionId: number, authorization?: string): Promise<Submission> {
    return apiClients.submissions.get('/api/submissions/:submission_id', {
      params: { submission_id: submissionId },
      headers: { authorization: authorization ?? undefined },
    }) as Promise<Submission>
  },
  async submit(exerciseSlug: string, sourceCode: string, authorization?: string): Promise<Submission> {
    return apiClients.submissions.post(
      '/api/submissions/exercises/:slug/submit',
      { source_code: sourceCode },
      {
        params: { slug: exerciseSlug },
        headers: { authorization: authorization ?? undefined },
      },
    ) as Promise<Submission>
  },
  async sendReviewChat(
    submissionId: number,
    message: string,
    history: ReviewChatMessage[],
    authorization?: string,
  ): Promise<{ answer: string }> {
    return apiClients.submissions.post(
      '/api/submissions/:submission_id/review-chat',
      { message, history },
      {
        params: { submission_id: submissionId },
        headers: { authorization: authorization ?? undefined },
      },
    ) as Promise<{ answer: string }>
  },
}
