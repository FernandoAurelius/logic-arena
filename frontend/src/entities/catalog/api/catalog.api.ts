import type { NavigatorResponse } from '@/entities/catalog'
import type { TrackDetail } from '@/entities/track'
import { apiClients, buildAuthHeaders } from '@/shared/api'

export const catalogApi = {
  async getNavigator(authorization?: string): Promise<NavigatorResponse> {
    return apiClients.catalog.get('/api/catalog/navigator', {
      headers: buildAuthHeaders(authorization),
    }) as Promise<NavigatorResponse>
  },
  async getTrackDetail(trackSlug: string, authorization?: string): Promise<TrackDetail> {
    return apiClients.catalog.get('/api/catalog/tracks/:track_slug', {
      params: { track_slug: trackSlug },
      headers: buildAuthHeaders(authorization),
    }) as Promise<TrackDetail>
  },
}
