export type ArenaSurfaceKey =
  | 'code_editor_single'
  | 'code_editor_multifile'
  | 'http_contract_lab'

export type ArenaSurfaceConfig = {
  label: string
  primaryActionLabel: string
  primaryActionBusyLabel: string
  outcomeNoun: string
  reviewPrompt: string
  specModeLabel: string
}

const DEFAULT_SURFACE_CONFIG: ArenaSurfaceConfig = {
  label: 'Código',
  primaryActionLabel: 'Executar',
  primaryActionBusyLabel: 'Executando...',
  outcomeNoun: 'testes',
  reviewPrompt: 'Pergunte sobre o erro, a melhoria ou o raciocínio esperado.',
  specModeLabel: 'Modo de prova',
}

export const ARENA_SURFACE_CONFIG: Record<ArenaSurfaceKey, ArenaSurfaceConfig> = {
  code_editor_single: DEFAULT_SURFACE_CONFIG,
  code_editor_multifile: {
    label: 'Código multiarquivo',
    primaryActionLabel: 'Executar',
    primaryActionBusyLabel: 'Executando...',
    outcomeNoun: 'testes',
    reviewPrompt: 'Pergunte sobre o erro, a integração entre arquivos ou o raciocínio esperado.',
    specModeLabel: 'Modo de projeto',
  },
  http_contract_lab: {
    label: 'Contrato HTTP',
    primaryActionLabel: 'Validar contrato',
    primaryActionBusyLabel: 'Validando...',
    outcomeNoun: 'assertivas',
    reviewPrompt: 'Pergunte sobre status, headers, corpo, schema ou divergências do contrato.',
    specModeLabel: 'Modo de contrato',
  },
}

function asRecord(value: unknown): Record<string, unknown> | null {
  if (typeof value !== 'object' || value === null || Array.isArray(value)) {
    return null
  }
  return value as Record<string, unknown>
}

function normalizeKey(value: unknown): string {
  return typeof value === 'string' ? value.trim().toLowerCase().replace(/\s+/g, '_') : ''
}

function readNestedString(source: Record<string, unknown> | null, key: string): string {
  if (!source) return ''
  return normalizeKey(source[key])
}

export function resolveArenaSurfaceKey(exercise: unknown): ArenaSurfaceKey {
  const record = asRecord(exercise)
  const workspaceSpec = asRecord(record?.workspace_spec ?? record?.workspaceSpec)
  const evaluationPlan = asRecord(record?.evaluation_plan ?? record?.evaluationPlan)

  const candidates = [
    normalizeKey(record?.surface_key),
    normalizeKey(record?.surfaceKey),
    readNestedString(workspaceSpec, 'surface_key'),
    readNestedString(workspaceSpec, 'surfaceKey'),
    normalizeKey(record?.family_key),
    normalizeKey(record?.familyKey),
    normalizeKey(record?.exercise_type_slug),
    normalizeKey(record?.exercise_type),
    readNestedString(evaluationPlan, 'surface_key'),
    readNestedString(evaluationPlan, 'surfaceKey'),
    normalizeKey(workspaceSpec?.workspace_kind),
    normalizeKey(workspaceSpec?.workspaceKind),
    normalizeKey(evaluationPlan?.template),
    normalizeKey(evaluationPlan?.template_key),
  ].filter(Boolean)

  if (candidates.some((candidate) => candidate.includes('http') || candidate.includes('contract'))) {
    return 'http_contract_lab'
  }

  if (
    candidates.some((candidate) => candidate.includes('multifile') || candidate.includes('multi_file'))
    || normalizeKey(workspaceSpec?.workspace_kind) === 'multifile'
    || normalizeKey(workspaceSpec?.workspaceKind) === 'multifile'
  ) {
    return 'code_editor_multifile'
  }

  return 'code_editor_single'
}

export function getArenaSurfaceConfig(surfaceKey: ArenaSurfaceKey | string | null | undefined): ArenaSurfaceConfig {
  if (surfaceKey === 'code_editor_multifile') return ARENA_SURFACE_CONFIG.code_editor_multifile
  if (surfaceKey === 'http_contract_lab') return ARENA_SURFACE_CONFIG.http_contract_lab
  return DEFAULT_SURFACE_CONFIG
}

export function isHttpContractSurface(surfaceKey: ArenaSurfaceKey | string | null | undefined): boolean {
  return surfaceKey === 'http_contract_lab'
}
