import { computed, ref } from 'vue'
import type { infer as ZodInfer } from 'zod'

import { schemas } from '@/lib/api/generated'
import { authApi } from '@/lib/api/client'

type User = ZodInfer<typeof schemas.UserSchema>
type LoginResponse = ZodInfer<typeof schemas.LoginResponseSchema>

const STORAGE_KEY = 'logic-arena-session'

const token = ref('')
const currentUser = ref<User | null>(null)
const initialized = ref(false)
const authBusy = ref(false)

const isAuthenticated = computed(() => Boolean(token.value && currentUser.value))

function authHeader() {
  return token.value ? `Bearer ${token.value}` : null
}

function persistSession(payload: { token: string; user: User }) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(payload))
}

function clearSession() {
  localStorage.removeItem(STORAGE_KEY)
  token.value = ''
  currentUser.value = null
}

async function hydrateSession() {
  if (!token.value) return

  try {
    const me = await authApi.get('/api/auth/me', {
      headers: { authorization: authHeader() ?? undefined },
    })
    currentUser.value = me
    persistSession({ token: token.value, user: me })
  } catch (error) {
    console.error(error)
    clearSession()
  }
}

async function initSession() {
  if (initialized.value) return
  initialized.value = true

  const savedSession = localStorage.getItem(STORAGE_KEY)
  if (!savedSession) return

  try {
    const parsed = JSON.parse(savedSession) as { token: string; user: User }
    token.value = parsed.token
    currentUser.value = parsed.user
    await hydrateSession()
  } catch (error) {
    console.error(error)
    clearSession()
  }
}

async function login(nickname: string, password: string): Promise<LoginResponse> {
  authBusy.value = true
  try {
    const response = (await authApi.post('/api/auth/login', {
      nickname: nickname.trim(),
      password,
    })) as LoginResponse
    token.value = response.token
    currentUser.value = response.user
    persistSession({ token: response.token, user: response.user })
    await hydrateSession()
    return response
  } finally {
    authBusy.value = false
  }
}

export function useSession() {
  return {
    token,
    currentUser,
    initialized,
    authBusy,
    isAuthenticated,
    authHeader,
    initSession,
    hydrateSession,
    login,
    clearSession,
  }
}
