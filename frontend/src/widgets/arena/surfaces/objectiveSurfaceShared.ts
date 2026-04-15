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

export type ObjectiveTemplateKey =
  | 'single-choice'
  | 'multi-select'
  | 'snippet-read-only'
  | 'compile-runtime-output'
  | 'behavior-classification'
  | 'output-prediction'

export type ObjectiveTemplateMeta = {
  key?: string
  title?: string
  stimulus_kind?: string
  response_shape?: string
  requires_output_text?: boolean
  response_input_label?: string
  response_input_placeholder?: string
  expected_output_text?: string
  analysis_steps?: string[]
  verdict_options?: Array<{ key: string; label: string }>
}

export type ObjectiveTemplateInfo = {
  key: ObjectiveTemplateKey
  badge: string
  title: string
  subtitle: string
  lens_title: string
  lens_copy: string
  review_title: string
  review_copy: string
  action_title: string
  action_copy: string
}

const objectiveTemplateInfo: Record<ObjectiveTemplateKey, ObjectiveTemplateInfo> = {
  'single-choice': {
    key: 'single-choice',
    badge: 'Resposta única',
    title: 'Escolha objetiva',
    subtitle: 'Uma alternativa correta entre distratores plausíveis.',
    lens_title: 'Leitura guiada',
    lens_copy: 'A alternativa correta precisa sobreviver à leitura literal do estímulo e ao conceito em jogo.',
    review_title: 'O que a IA observa',
    review_copy: 'Gabarito, misconception tag e justificativa da escolha mais provável para o erro.',
    action_title: 'Decisão',
    action_copy: 'Uma seleção deve permanecer marcada.',
  },
  'multi-select': {
    key: 'multi-select',
    badge: 'Resposta múltipla',
    title: 'Escolha múltipla',
    subtitle: 'Mais de uma alternativa pode estar correta.',
    lens_title: 'Discriminação conceitual',
    lens_copy: 'Cada afirmação precisa ser tratada como um teste separado, não como uma impressão geral.',
    review_title: 'O que a IA observa',
    review_copy: 'Cobertura parcial, omission errors e conceitos que ficaram de fora da seleção.',
    action_title: 'Cobertura',
    action_copy: 'Todas as alternativas corretas precisam aparecer na resposta.',
  },
  'snippet-read-only': {
    key: 'snippet-read-only',
    badge: 'Snippet read-only',
    title: 'Leitura de evidência',
    subtitle: 'O estímulo é imutável e a decisão vem da interpretação cuidadosa.',
    lens_title: 'Estímulo fixo',
    lens_copy: 'O trecho não pode ser editado; a superfície mede leitura, comparação e reconhecimento de comportamento.',
    review_title: 'O que a IA observa',
    review_copy: 'Se o aluno leu a evidência antes de responder e qual pista conceitual guiou a escolha.',
    action_title: 'Interpretação',
    action_copy: 'A resposta nasce da leitura do código, não da escrita de uma nova solução.',
  },
  'compile-runtime-output': {
    key: 'compile-runtime-output',
    badge: 'Compile / Runtime / Output',
    title: 'Diagnóstico de execução',
    subtitle: 'Separe compilação, runtime e saída observável antes de classificar.',
    lens_title: 'Três camadas',
    lens_copy: 'A superfície força a distinguir o que falha antes da execução, o que falha durante e o que aparece no output.',
    review_title: 'O que a IA observa',
    review_copy: 'A regra da linguagem que define o veredito, além do ponto exato em que o raciocínio descarrilou.',
    action_title: 'Classificação',
    action_copy: 'A resposta precisa refletir a etapa correta da falha ou da saída.',
  },
  'behavior-classification': {
    key: 'behavior-classification',
    badge: 'Behavior classification',
    title: 'Comportamento observável',
    subtitle: 'Analise despacho, herança e efeitos colaterais com precisão.',
    lens_title: 'Comportamento',
    lens_copy: 'O snippet pode compilar, mas a semântica real depende de override, dispatch e exceções.',
    review_title: 'O que a IA observa',
    review_copy: 'A diferença entre o que o código parece fazer e o comportamento realmente evidenciado.',
    action_title: 'Veredito',
    action_copy: 'A resposta precisa capturar o comportamento emergente, não apenas a leitura superficial.',
  },
  'output-prediction': {
    key: 'output-prediction',
    badge: 'Output prediction',
    title: 'Previsão de saída',
    subtitle: 'Simule a execução e escolha a saída observável correta.',
    lens_title: 'Execução mental',
    lens_copy: 'O objetivo é prever a saída final com precisão, linha a linha, sem editar o código.',
    review_title: 'O que a IA observa',
    review_copy: 'A ordem da execução, os valores intermediários e o ponto exato em que a previsão se desvia.',
    action_title: 'Saída esperada',
    action_copy: 'A resposta deve refletir a saída real do snippet, não a intenção aparente do código.',
  },
}

export function getObjectiveWorkspace(sessionConfig?: SessionConfig | null) {
  return (sessionConfig?.workspace_spec ?? {}) as Record<string, unknown>
}

export function formatAttemptMode(mode?: string | null) {
  const normalized = String(mode ?? '').trim().toLowerCase()
  if (normalized === 'practice') return 'Prática'
  if (normalized === 'checkpoint') return 'Checkpoint'
  if (normalized === 'exam') return 'Simulado'
  if (normalized === 'review') return 'Revisão'
  return normalized || 'Prática'
}

export function getObjectiveTemplateKey(sessionConfig?: SessionConfig | null): ObjectiveTemplateKey {
  const workspace = getObjectiveWorkspace(sessionConfig)
  const template = String(workspace.template ?? '').trim().toLowerCase()

  if (template === 'multi-select' || template === 'multi_select') return 'multi-select'
  if (
    template === 'snippet-read-only'
    || template === 'read-only-snippet'
    || template === 'snippet-analysis'
    || template === 'code-snippet'
  ) {
    return 'snippet-read-only'
  }
  if (template === 'compile-runtime-output') return 'compile-runtime-output'
  if (template === 'behavior-classification') return 'behavior-classification'
  if (template === 'output-prediction' || template === 'output_prediction') return 'output-prediction'
  if (template === 'single-choice' || template === 'single_choice') return 'single-choice'

  return Boolean(workspace.allow_multiple) || String(workspace.choice_mode ?? '') === 'multiple'
    ? 'multi-select'
    : 'single-choice'
}

export function getObjectiveTemplateInfo(sessionConfig?: SessionConfig | null): ObjectiveTemplateInfo {
  return objectiveTemplateInfo[getObjectiveTemplateKey(sessionConfig)]
}

export function getObjectiveTemplateMeta(sessionConfig?: SessionConfig | null): ObjectiveTemplateMeta {
  const workspace = getObjectiveWorkspace(sessionConfig)
  const templateMeta = workspace.template_meta
  if (!templateMeta || typeof templateMeta !== 'object') return {}
  return templateMeta as ObjectiveTemplateMeta
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
  const code = String(workspace.snippet ?? '')
  return {
    code,
    language: String(workspace.snippet_language ?? 'python'),
    readOnly: Boolean(workspace.snippet_read_only),
    template: getObjectiveTemplateKey(sessionConfig),
    title: String(workspace.snippet_title ?? workspace.snippet_filename ?? 'Trecho de referência'),
    lineCount: code ? code.split(/\r?\n/).length : 0,
  }
}

export function getObjectiveStatement(sessionConfig?: SessionConfig | null) {
  const exercise = sessionConfig?.exercise
  return String(
    exercise?.statement
      || exercise?.pedagogical_brief
      || exercise?.concept_summary
      || exercise?.professor_note
      || 'Leia o estímulo e selecione a melhor resposta.',
  ).trim()
}

export function getObjectiveLearningObjectives(sessionConfig?: SessionConfig | null) {
  const exercise = sessionConfig?.exercise
  const learningObjectives = Array.isArray(exercise?.learning_objectives) ? exercise.learning_objectives : []
  const filtered = learningObjectives.map((item) => String(item).trim()).filter(Boolean)
  if (filtered.length > 0) return filtered

  const fallback = [exercise?.concept_summary, exercise?.pedagogical_brief]
    .map((item) => String(item ?? '').trim())
    .filter(Boolean)
  return fallback.length > 0 ? fallback : ['leitura guiada', 'discriminação conceitual']
}

export function getObjectiveContextTags(sessionConfig?: SessionConfig | null) {
  const exercise = sessionConfig?.exercise
  const tags = [
    exercise?.difficulty,
    exercise?.review_profile,
    sessionConfig?.mode,
  ]
    .map((item) => String(item ?? '').trim())
    .filter(Boolean)
  return Array.from(new Set(tags))
}

export function getObjectiveSelectedOptionDetails(
  sessionConfig?: SessionConfig | null,
  selectedOptions: string[] = [],
) {
  const options = getObjectiveOptions(sessionConfig)
  return selectedOptions
    .map((selected) => options.find((option) => (option.canonical_key ?? option.key) === selected))
    .filter((option): option is ObjectiveOption => Boolean(option))
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
