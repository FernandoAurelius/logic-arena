import { computed, ref } from 'vue'

type ThemeMode = 'light' | 'dark'

const STORAGE_KEY = 'logic-arena-theme'
const theme = ref<ThemeMode>('light')
let initialized = false

function applyTheme(nextTheme: ThemeMode) {
  if (typeof document === 'undefined') return
  document.documentElement.dataset.theme = nextTheme
  document.documentElement.style.colorScheme = nextTheme
}

function detectInitialTheme(): ThemeMode {
  if (typeof window === 'undefined') return 'light'
  const stored = window.localStorage.getItem(STORAGE_KEY)
  if (stored === 'light' || stored === 'dark') return stored
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

export function useTheme() {
  function initTheme() {
    if (initialized) {
      applyTheme(theme.value)
      return
    }
    theme.value = detectInitialTheme()
    applyTheme(theme.value)
    initialized = true
  }

  function setTheme(nextTheme: ThemeMode) {
    theme.value = nextTheme
    applyTheme(nextTheme)
    if (typeof window !== 'undefined') {
      window.localStorage.setItem(STORAGE_KEY, nextTheme)
    }
  }

  function toggleTheme() {
    setTheme(theme.value === 'light' ? 'dark' : 'light')
  }

  return {
    theme,
    isDark: computed(() => theme.value === 'dark'),
    initTheme,
    setTheme,
    toggleTheme,
  }
}
