import type { infer as ZodInfer } from 'zod'

import type { TrackDetail } from '@/entities/track'
import { schemas } from '@/shared/api/generated'
import { apiClients } from '@/shared/api/zodios'

type NavigatorResponse = ZodInfer<typeof schemas.NavigatorResponseSchema>

export const catalogApi = {
  async getNavigator(authorization?: string): Promise<NavigatorResponse> {
    return apiClients.catalog.get('/api/catalog/navigator', {
      headers: { authorization: authorization ?? undefined },
    }) as Promise<NavigatorResponse>
  },
  async getTrackDetail(trackSlug: string, authorization?: string): Promise<TrackDetail> {
    return apiClients.catalog.get('/api/catalog/tracks/:track_slug', {
      params: { track_slug: trackSlug },
      headers: { authorization: authorization ?? undefined },
    }) as Promise<TrackDetail>
  },
}
