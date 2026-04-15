export type ArenaSurfaceKey =
  | 'code_editor_single'
  | 'code_editor_multifile'
  | 'objective_choices'
  | 'objective_classifier'
  | 'restricted_diff'
  | 'restricted_fill_blanks'
  | 'http_contract_lab'
  | 'component_behavior_lab'
  | 'guided_text_response'

export type ArenaSurfaceKind = 'code' | 'objective' | 'restricted' | 'contract' | 'guided'

export type ArenaSurfaceDescriptor = {
  key: ArenaSurfaceKey
  title: string
  description: string
  kind: ArenaSurfaceKind
  implemented: boolean
  anatomy: string[]
  accent: string
}

const surfaceDescriptors: Record<ArenaSurfaceKey, ArenaSurfaceDescriptor> = {
  code_editor_single: {
    key: 'code_editor_single',
    title: 'Editor único',
    description: 'Fluxo canônico de código executável com uma superfície principal de trabalho.',
    kind: 'code',
    implemented: true,
    anatomy: ['editor', 'console', 'checagem', 'revisão'],
    accent: 'primary',
  },
  code_editor_multifile: {
    key: 'code_editor_multifile',
    title: 'Workspace multi-arquivo',
    description: 'Lab de código com arquivos e abas múltiplas, pronto para projetos mais ricos.',
    kind: 'code',
    implemented: true,
    anatomy: ['arquivos', 'abas', 'editor', 'console'],
    accent: 'primary',
  },
  objective_choices: {
    key: 'objective_choices',
    title: 'Escolha objetiva',
    description: 'Itens com estímulo read-only, alternativas fixas e revisão ancorada em gabarito.',
    kind: 'objective',
    implemented: true,
    anatomy: ['estímulo', 'alternativas', 'gabarito', 'mentor'],
    accent: 'amber',
  },
  objective_classifier: {
    key: 'objective_classifier',
    title: 'Classificador de comportamento',
    description: 'Questões de compile/runtime/output e behavior classification com veredito objetivo.',
    kind: 'objective',
    implemented: true,
    anatomy: ['snippet', 'classificação', 'veredito', 'output'],
    accent: 'amber',
  },
  restricted_diff: {
    key: 'restricted_diff',
    title: 'Diff guiado',
    description: 'Correção localizada com regiões editáveis e evidência estrutural de mudança.',
    kind: 'restricted',
    implemented: true,
    anatomy: ['original', 'patch', 'regiões bloqueadas', 'validação'],
    accent: 'teal',
  },
  restricted_fill_blanks: {
    key: 'restricted_fill_blanks',
    title: 'Lacunas editáveis',
    description: 'Preenchimento guiado com slots controlados e feedback por bloco.',
    kind: 'restricted',
    implemented: true,
    anatomy: ['lacunas', 'slots', 'checagem', 'explicação'],
    accent: 'teal',
  },
  http_contract_lab: {
    key: 'http_contract_lab',
    title: 'Contrato HTTP',
    description: 'Lab de API com request, response, schema e divergências observáveis.',
    kind: 'contract',
    implemented: false,
    anatomy: ['request', 'response', 'schema', 'assertions'],
    accent: 'violet',
  },
  component_behavior_lab: {
    key: 'component_behavior_lab',
    title: 'Comportamento de componente',
    description: 'Preview de UI, estado e DOM para contratos de frontend mais ricos.',
    kind: 'contract',
    implemented: false,
    anatomy: ['props', 'preview', 'estado', 'DOM'],
    accent: 'violet',
  },
  guided_text_response: {
    key: 'guided_text_response',
    title: 'Resposta guiada',
    description: 'Resposta discursiva com rubrica, checkpoints e revisão assistida por IA.',
    kind: 'guided',
    implemented: false,
    anatomy: ['prompt', 'rubrica', 'resposta', 'revisão'],
    accent: 'slate',
  },
}

const fallbackSurface: ArenaSurfaceDescriptor = {
  key: 'code_editor_single',
  title: 'Editor único',
  description: 'Fluxo canônico de código executável com uma superfície principal de trabalho.',
  kind: 'code',
  implemented: true,
  anatomy: ['editor', 'console', 'checagem', 'revisão'],
  accent: 'primary',
}

export function getArenaSurfaceDescriptor(surfaceKey?: string | null): ArenaSurfaceDescriptor {
  if (!surfaceKey) return fallbackSurface
  return surfaceDescriptors[surfaceKey as ArenaSurfaceKey] ?? {
    key: surfaceKey as ArenaSurfaceKey,
    title: 'Superfície desconhecida',
    description: 'A Arena reconhece o contrato, mas ainda não há um renderer registrado.',
    kind: 'guided',
    implemented: false,
    anatomy: ['registro', 'renderer', 'feedback', 'revisão'],
    accent: 'slate',
  }
}

export const arenaSurfaceDescriptors = surfaceDescriptors
