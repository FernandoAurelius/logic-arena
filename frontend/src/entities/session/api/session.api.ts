import type { infer as ZodInfer } from 'zod'

import { apiClients, schemas } from '@/shared/api'

type LoginResponse = ZodInfer<typeof schemas.LoginResponseSchema>
type User = ZodInfer<typeof schemas.UserSchema>

export const sessionApi = {
  async login(payload: { nickname: string; password: string }): Promise<LoginResponse> {
    return apiClients.auth.post('/api/auth/login', payload) as Promise<LoginResponse>
  },
  async me(authorization?: string): Promise<User> {
    return apiClients.auth.get('/api/auth/me', {
      headers: { authorization: authorization ?? undefined },
    }) as Promise<User>
  },
}
