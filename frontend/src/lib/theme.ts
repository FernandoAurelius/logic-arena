import { computed, ref } from 'vue'

export type ThemeMode = 'light' | 'dark'
export type ThemeAccent = 'ember' | 'ocean' | 'forest' | 'amber'

type ThemeAccentTokens = {
  primary: string
  primaryContainer: string
  surfaceTint: string
  primaryFixed: string
  primaryFixedDim: string
  onPrimaryFixed: string
  outlineVariant: string
  gridLine: string
  gridLineStrong: string
}

type ThemePreset = {
  id: ThemeAccent
  label: string
  description: string
  tokens: ThemeAccentTokens
}

const MODE_STORAGE_KEY = 'logic-arena-theme-mode'
const ACCENT_STORAGE_KEY = 'logic-arena-theme-accent'
const LEGACY_STORAGE_KEY = 'logic-arena-theme'

const DEFAULT_MODE: ThemeMode = 'light'
const DEFAULT_ACCENT: ThemeAccent = 'ember'

const theme = ref<ThemeMode>(DEFAULT_MODE)
const accent = ref<ThemeAccent>(DEFAULT_ACCENT)
let initialized = false

const accentPresets: ThemePreset[] = [
  {
    id: 'ember',
    label: 'Ember',
    description: 'Acento quente, próximo da identidade atual.',
    tokens: {
      primary: '#b52701',
      primaryContainer: '#ff5c35',
      surfaceTint: '#b52701',
      primaryFixed: '#ffdad2',
      primaryFixedDim: '#ffb4a3',
      onPrimaryFixed: '#3d0700',
      outlineVariant: '#e3beb6',
      gridLine: 'rgba(143, 112, 105, 0.12)',
      gridLineStrong: 'rgba(143, 112, 105, 0.15)',
    },
  },
  {
    id: 'ocean',
    label: 'Ocean',
    description: 'Mais frio e técnico, com azul como cor principal.',
    tokens: {
      primary: '#0f5bb5',
      primaryContainer: '#4fa3ff',
      surfaceTint: '#0f5bb5',
      primaryFixed: '#d6e8ff',
      primaryFixedDim: '#9cc7ff',
      onPrimaryFixed: '#001c3d',
      outlineVariant: '#b6cbe3',
      gridLine: 'rgba(74, 103, 143, 0.12)',
      gridLineStrong: 'rgba(74, 103, 143, 0.16)',
    },
  },
  {
    id: 'forest',
    label: 'Forest',
    description: 'Verde sóbrio para uma sensação mais de progresso e estabilidade.',
    tokens: {
      primary: '#1f7a49',
      primaryContainer: '#58b57b',
      surfaceTint: '#1f7a49',
      primaryFixed: '#d8f4e1',
      primaryFixedDim: '#a8ddb9',
      onPrimaryFixed: '#0a2f1b',
      outlineVariant: '#bdd6c4',
      gridLine: 'rgba(92, 129, 102, 0.12)',
      gridLineStrong: 'rgba(92, 129, 102, 0.16)',
    },
  },
  {
    id: 'amber',
    label: 'Amber',
    description: 'Mais dourado e caloroso, com sensação de destaque e recompensa.',
    tokens: {
      primary: '#b86a00',
      primaryContainer: '#ffb347',
      surfaceTint: '#b86a00',
      primaryFixed: '#ffe4b8',
      primaryFixedDim: '#f7c56c',
      onPrimaryFixed: '#3d2500',
      outlineVariant: '#e2c496',
      gridLine: 'rgba(176, 129, 45, 0.12)',
      gridLineStrong: 'rgba(176, 129, 45, 0.16)',
    },
  },
]

function getRootElement() {
  return typeof document === 'undefined' ? null : document.documentElement
}

function applyAccentTokens(preset: ThemePreset) {
  const root = getRootElement()
  if (!root) return

  const { tokens } = preset
  root.style.setProperty('--primary', tokens.primary)
  root.style.setProperty('--primary-container', tokens.primaryContainer)
  root.style.setProperty('--surface-tint', tokens.surfaceTint)
  root.style.setProperty('--primary-fixed', tokens.primaryFixed)
  root.style.setProperty('--primary-fixed-dim', tokens.primaryFixedDim)
  root.style.setProperty('--on-primary-fixed', tokens.onPrimaryFixed)
  root.style.setProperty('--outline-variant', tokens.outlineVariant)
  root.style.setProperty('--grid-line', tokens.gridLine)
  root.style.setProperty('--grid-line-strong', tokens.gridLineStrong)
}

function applyTheme(nextTheme: ThemeMode, nextAccent: ThemeAccent) {
  const root = getRootElement()
  if (!root) return

  const preset = accentPresets.find((candidate) => candidate.id === nextAccent) ?? accentPresets[0]

  root.dataset.theme = nextTheme
  root.dataset.themeMode = nextTheme
  root.dataset.themeAccent = preset.id
  root.style.colorScheme = nextTheme

  applyAccentTokens(preset)
}

function detectInitialTheme(): ThemeMode {
  if (typeof window === 'undefined') return DEFAULT_MODE
  const mode = window.localStorage.getItem(MODE_STORAGE_KEY) ?? window.localStorage.getItem(LEGACY_STORAGE_KEY)
  if (mode === 'light' || mode === 'dark') return mode
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

function detectInitialAccent(): ThemeAccent {
  if (typeof window === 'undefined') return DEFAULT_ACCENT
  const stored = window.localStorage.getItem(ACCENT_STORAGE_KEY)
  if (stored && accentPresets.some((preset) => preset.id === stored)) return stored as ThemeAccent
  return DEFAULT_ACCENT
}

function persistTheme(mode: ThemeMode, nextAccent: ThemeAccent) {
  if (typeof window === 'undefined') return
  window.localStorage.setItem(MODE_STORAGE_KEY, mode)
  window.localStorage.setItem(LEGACY_STORAGE_KEY, mode)
  window.localStorage.setItem(ACCENT_STORAGE_KEY, nextAccent)
}

function normalizeAccent(nextAccent: ThemeAccent | string): ThemeAccent {
  return accentPresets.some((preset) => preset.id === nextAccent) ? (nextAccent as ThemeAccent) : DEFAULT_ACCENT
}

export function useTheme() {
  function initTheme() {
    if (initialized) {
      applyTheme(theme.value, accent.value)
      return
    }
    theme.value = detectInitialTheme()
    accent.value = detectInitialAccent()
    applyTheme(theme.value, accent.value)
    initialized = true
  }

  function setTheme(nextTheme: ThemeMode) {
    theme.value = nextTheme
    applyTheme(nextTheme, accent.value)
    persistTheme(nextTheme, accent.value)
  }

  function setThemeMode(nextTheme: ThemeMode) {
    setTheme(nextTheme)
  }

  function toggleTheme() {
    setTheme(theme.value === 'light' ? 'dark' : 'light')
  }

  function setAccent(nextAccent: ThemeAccent | string) {
    accent.value = normalizeAccent(nextAccent)
    applyTheme(theme.value, accent.value)
    persistTheme(theme.value, accent.value)
  }

  return {
    theme,
    accent,
    isDark: computed(() => theme.value === 'dark'),
    modeOptions: computed(() =>
      (['light', 'dark'] as ThemeMode[]).map((mode) => ({
        id: mode,
        label: mode === 'light' ? 'Claro' : 'Escuro',
      })),
    ),
    accentOptions: computed(() => accentPresets.map(({ id, label, description }) => ({ id, label, description }))),
    activeAccent: computed(() => accent.value),
    initTheme,
    setTheme,
    setThemeMode,
    toggleTheme,
    setAccent,
  }
}

