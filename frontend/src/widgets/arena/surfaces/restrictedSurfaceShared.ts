import type { SessionConfig } from '@/entities/practice-session'

export type RestrictedBlank = {
  key: string
  label: string
  placeholder: string
  hint: string
}

const BLANK_TOKEN = /\[\[blank:([a-zA-Z0-9_-]+)\]\]/g

export function getRestrictedWorkspaceSpec(sessionConfig?: SessionConfig | null) {
  return (sessionConfig?.workspace_spec ?? {}) as Record<string, any>
}

export function getRestrictedTemplate(sessionConfig?: SessionConfig | null) {
  return String(getRestrictedWorkspaceSpec(sessionConfig).template ?? 'fix-the-snippet')
}

export function getRestrictedLanguage(sessionConfig?: SessionConfig | null) {
  return String(getRestrictedWorkspaceSpec(sessionConfig).language ?? 'python')
}

export function getRestrictedOriginalCode(sessionConfig?: SessionConfig | null) {
  const workspace = getRestrictedWorkspaceSpec(sessionConfig)
  return String(workspace.original_code ?? workspace.editable_code ?? '')
}

export function getRestrictedEditableCode(sessionConfig?: SessionConfig | null) {
  const workspace = getRestrictedWorkspaceSpec(sessionConfig)
  return String(workspace.editable_code ?? workspace.original_code ?? '')
}

export function getRestrictedBlankTemplate(sessionConfig?: SessionConfig | null) {
  const workspace = getRestrictedWorkspaceSpec(sessionConfig)
  return String(workspace.blank_template ?? workspace.editable_code ?? '')
}

export function getRestrictedInstructions(sessionConfig?: SessionConfig | null) {
  return String(getRestrictedWorkspaceSpec(sessionConfig).instructions ?? '')
}

export function getRestrictedTemplateMeta(sessionConfig?: SessionConfig | null) {
  return (getRestrictedWorkspaceSpec(sessionConfig).template_meta ?? {}) as Record<string, any>
}

export function getRestrictedBlanks(sessionConfig?: SessionConfig | null): RestrictedBlank[] {
  const raw = getRestrictedWorkspaceSpec(sessionConfig).blanks
  if (!Array.isArray(raw)) return []
  return raw.map((blank, index) => ({
    key: String(blank?.key ?? blank?.id ?? `blank-${index + 1}`),
    label: String(blank?.label ?? blank?.placeholder ?? `Lacuna ${index + 1}`),
    placeholder: String(blank?.placeholder ?? ''),
    hint: String(blank?.hint ?? ''),
  }))
}

export function extractBlankAnswers(templateSource: string, renderedSource: string) {
  const keys = Array.from(templateSource.matchAll(BLANK_TOKEN)).map((match) => match[1])
  if (keys.length === 0) return {} as Record<string, string>

  const patternParts: string[] = []
  let cursor = 0
  for (const match of templateSource.matchAll(BLANK_TOKEN)) {
    patternParts.push(escapeRegex(templateSource.slice(cursor, match.index ?? 0)))
    patternParts.push(`(?<${match[1]}>[\\s\\S]*?)`)
    cursor = (match.index ?? 0) + match[0].length
  }
  patternParts.push(escapeRegex(templateSource.slice(cursor)))
  const matched = new RegExp(`^${patternParts.join('')}$`, 'm').exec(renderedSource)
  if (!matched?.groups) return {} as Record<string, string>

  return keys.reduce<Record<string, string>>((accumulator, key) => {
    accumulator[key] = String(matched.groups?.[key] ?? '')
    return accumulator
  }, {})
}

export function renderBlankTemplate(templateSource: string, answers: Record<string, string>) {
  return String(templateSource ?? '').replace(BLANK_TOKEN, (_, key: string) => answers[key] ?? '')
}

function escapeRegex(value: string) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}
