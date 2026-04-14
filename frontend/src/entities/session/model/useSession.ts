import { computed, ref } from 'vue'
import type { infer as ZodInfer } from 'zod'

import { schemas } from '@/shared/api'
import { sessionApi } from '@/entities/session/api/session.api'

type User = ZodInfer<typeof schemas.UserSchema>
type LoginResponse = ZodInfer<typeof schemas.LoginResponseSchema>
type UserProgressSummary = ZodInfer<typeof schemas.UserProgressSummarySchema>

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

function setCurrentUser(user: User | null) {
  currentUser.value = user
  if (token.value && user) {
    persistSession({ token: token.value, user })
  }
}

function clearSession() {
  localStorage.removeItem(STORAGE_KEY)
  token.value = ''
  currentUser.value = null
}

async function hydrateSession() {
  if (!token.value) return

  try {
    const me = await sessionApi.me(authHeader() ?? undefined)
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
    const response = await sessionApi.login({
      nickname: nickname.trim(),
      password,
    })
    token.value = response.token
    currentUser.value = response.user
    persistSession({ token: response.token, user: response.user })
    await hydrateSession()
    return response
  } finally {
    authBusy.value = false
  }
}

function mergeCurrentUserProgress(progress: UserProgressSummary) {
  if (!currentUser.value) return
  setCurrentUser({
    ...currentUser.value,
    xp_total: progress.xp_total,
    level: progress.level,
    xp_into_level: progress.xp_into_level,
    xp_to_next_level: progress.xp_to_next_level,
  })
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
    setCurrentUser,
    mergeCurrentUserProgress,
  }
}
