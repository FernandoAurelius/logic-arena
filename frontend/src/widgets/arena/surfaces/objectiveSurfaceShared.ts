import type { SessionConfig } from '@/entities/practice-session'

export type ObjectiveOption = {
  key: string
  canonical_key?: string
  label: string
  explanation?: string
  is_correct?: boolean
  correct?: boolean
  misconception_tag?: string
  aliases?: string[]
}

export function getObjectiveWorkspace(sessionConfig?: SessionConfig | null) {
  return (sessionConfig?.workspace_spec ?? {}) as Record<string, unknown>
}

export function getObjectiveOptions(sessionConfig?: SessionConfig | null): ObjectiveOption[] {
  const workspace = getObjectiveWorkspace(sessionConfig)
  const options = workspace.options
  if (!Array.isArray(options)) return []
  return options
    .filter((option): option is Record<string, unknown> => Boolean(option) && typeof option === 'object')
    .map((option) => ({
      key: String(option.key ?? option.canonical_key ?? ''),
      canonical_key: String(option.canonical_key ?? option.key ?? ''),
      label: String(option.label ?? option.key ?? option.canonical_key ?? 'Alternativa'),
      explanation: option.explanation ? String(option.explanation) : undefined,
      is_correct: Boolean(option.is_correct),
      correct: Boolean(option.correct),
      misconception_tag: option.misconception_tag ? String(option.misconception_tag) : undefined,
      aliases: Array.isArray(option.aliases) ? option.aliases.map((alias) => String(alias)) : [],
    }))
}

export function isObjectiveMultiple(sessionConfig?: SessionConfig | null) {
  const workspace = getObjectiveWorkspace(sessionConfig)
  return Boolean(workspace.allow_multiple) || String(workspace.choice_mode ?? '') === 'multiple'
}

export function getObjectiveSnippet(sessionConfig?: SessionConfig | null) {
  const workspace = getObjectiveWorkspace(sessionConfig)
  return {
    code: String(workspace.snippet ?? ''),
    language: String(workspace.snippet_language ?? 'python'),
    readOnly: Boolean(workspace.snippet_read_only),
    template: String(workspace.template ?? 'single-choice'),
  }
}

export function toggleObjectiveSelection(
  current: string[],
  key: string,
  allowMultiple: boolean,
) {
  if (!allowMultiple) {
    return current[0] === key ? [] : [key]
  }

  if (current.includes(key)) {
    return current.filter((item) => item !== key)
  }
  return [...current, key]
}
