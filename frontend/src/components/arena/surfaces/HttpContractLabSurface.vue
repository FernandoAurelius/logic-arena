<script setup lang="ts">
import { computed, ref, watch } from 'vue'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'

import { ARENA_SURFACE_CONFIG } from './arenaSurfaceRegistry'

type ContractRecord = Record<string, unknown>

const props = defineProps<{
  modelValue?: string
  exerciseTitle?: string
  workspaceSpec?: unknown
  evaluationPlan?: unknown
  readOnly?: boolean
}>()

const emit = defineEmits<{
  (event: 'update:modelValue', value: string): void
}>()

const config = ARENA_SURFACE_CONFIG.http_contract_lab
const validationReady = ref(false)
const isHydrating = ref(false)

function asRecord(value: unknown): ContractRecord | null {
  if (typeof value !== 'object' || value === null || Array.isArray(value)) return null
  return value as ContractRecord
}

function readString(value: unknown, fallback = '') {
  if (typeof value === 'string') return value.trim()
  if (typeof value === 'number' || typeof value === 'boolean') return String(value)
  return fallback
}

function readArray(value: unknown): string[] {
  if (Array.isArray(value)) {
    return value
      .flatMap((item) => {
        if (typeof item === 'string') return [item.trim()]
        if (item && typeof item === 'object') {
          return [Object.entries(item as Record<string, unknown>).map(([key, val]) => `${key}: ${readString(val)}`).join(' · ')]
        }
        return [readString(item)]
      })
      .filter(Boolean)
  }

  if (typeof value === 'string') {
    return value
      .split('\n')
      .map((line) => line.trim())
      .filter(Boolean)
  }

  if (value && typeof value === 'object') {
    return Object.entries(value as Record<string, unknown>)
      .map(([key, val]) => `${key}: ${readString(val)}`)
      .filter(Boolean)
  }

  return []
}

function readNumber(value: unknown, fallback = 200) {
  if (typeof value === 'number' && Number.isFinite(value)) return value
  if (typeof value === 'string' && value.trim()) {
    const parsed = Number.parseInt(value, 10)
    if (!Number.isNaN(parsed)) return parsed
  }
  return fallback
}

function prettyJson(value: unknown, fallback = '') {
  if (typeof value === 'string') {
    const trimmed = value.trim()
    if (!trimmed) return fallback
    try {
      return JSON.stringify(JSON.parse(trimmed), null, 2)
    } catch {
      return value
    }
  }

  if (value && typeof value === 'object') {
    try {
      return JSON.stringify(value, null, 2)
    } catch {
      return fallback
    }
  }

  return fallback
}

function normalizeContractSource() {
  const root = asRecord(props.workspaceSpec) ?? {}
  const contract = asRecord(root.http_contract) ?? asRecord(root.contract) ?? root
  const request = asRecord(contract.request) ?? asRecord(root.request) ?? {}
  const response = asRecord(contract.response) ?? asRecord(root.response) ?? {}
  const evaluation = asRecord(props.evaluationPlan) ?? {}

  return {
    title: readString(contract.title, props.exerciseTitle || 'Contrato HTTP'),
    method: readString(contract.method || request.method, 'POST').toUpperCase(),
    path: readString(contract.path || request.path, '/api/contrato'),
    requestHeaders: readArray(contract.request_headers || request.headers || ['Content-Type: application/json']),
    requestBody: prettyJson(contract.request_body || request.body || '{\n  "resource": "logic-arena"\n}', '{\n  "resource": "logic-arena"\n}'),
    expectedStatus: readNumber(contract.expected_status || response.status, 200),
    expectedHeaders: readArray(contract.expected_headers || response.headers || ['Content-Type: application/json']),
    expectedBody: prettyJson(contract.expected_body || response.body || '{\n  "ok": true\n}', '{\n  "ok": true\n}'),
    responseSchema: readString(contract.response_schema || response.schema || 'application/json'),
    validationRules: readArray(contract.validation_rules || evaluation.validation_rules || evaluation.comparison_rules || [
      'status',
      'headers',
      'schema',
      'body',
    ]),
    comparisonHints: readArray(contract.comparison_hints || evaluation.review_hints || [
      'Conferir se o status preserva o contrato.',
      'Comparar headers e schema antes de aceitar o body.',
      'Ler a resposta como um acordo entre camadas, não como texto solto.',
    ]),
  }
}

const contract = computed(() => normalizeContractSource())

const requestMethod = ref('')
const requestPath = ref('')
const requestHeaders = ref('')
const requestBody = ref('')
const observedStatus = ref('')
const observedHeaders = ref('')
const observedBody = ref('')

function hydrateFromContract() {
  const normalized = contract.value
  isHydrating.value = true

  requestMethod.value = normalized.method
  requestPath.value = normalized.path
  requestHeaders.value = normalized.requestHeaders.join('\n')
  requestBody.value = normalized.requestBody
  observedStatus.value = ''
  observedHeaders.value = ''
  observedBody.value = ''
  validationReady.value = false

  if (props.modelValue?.trim()) {
    try {
      const parsed = JSON.parse(props.modelValue) as Record<string, unknown>
      requestMethod.value = readString(parsed.request_method || parsed.method, requestMethod.value).toUpperCase()
      requestPath.value = readString(parsed.request_path || parsed.path, requestPath.value)
      requestHeaders.value = readArray(parsed.request_headers || parsed.headers).join('\n') || requestHeaders.value
      requestBody.value = prettyJson(parsed.request_body || parsed.body, requestBody.value)
      observedStatus.value = readString(parsed.observed_status || parsed.response_status || '', observedStatus.value)
      observedHeaders.value = readArray(parsed.observed_headers || parsed.response_headers).join('\n')
      observedBody.value = prettyJson(parsed.observed_body || parsed.response_body, observedBody.value)
      validationReady.value = Boolean(parsed.validation_ready)
    } catch {
      requestBody.value = props.modelValue ?? ''
    }
  }

  isHydrating.value = false
  emitSerializedDraft()
}

function emitSerializedDraft() {
  if (isHydrating.value) return
  emit('update:modelValue', JSON.stringify({
    surface_key: 'http_contract_lab',
    request_method: requestMethod.value.trim().toUpperCase(),
    request_path: requestPath.value.trim(),
    request_headers: requestHeaders.value,
    request_body: requestBody.value,
    expected_status: contract.value.expectedStatus,
    expected_headers: contract.value.expectedHeaders,
    expected_body: contract.value.expectedBody,
    response_schema: contract.value.responseSchema,
    observed_status: observedStatus.value.trim(),
    observed_headers: observedHeaders.value,
    observed_body: observedBody.value,
    validation_ready: validationReady.value,
  }, null, 2))
}

watch(
  () => [props.workspaceSpec, props.evaluationPlan, props.exerciseTitle],
  () => hydrateFromContract(),
  { immediate: true, deep: true },
)

watch(
  () => props.modelValue,
  (nextValue) => {
    if (isHydrating.value) return
    if (!nextValue || nextValue.trim() === '' || nextValue === requestBody.value) return
    hydrateFromContract()
  },
)

watch(
  () => [requestMethod.value, requestPath.value, requestHeaders.value, requestBody.value, observedStatus.value, observedHeaders.value, observedBody.value],
  () => emitSerializedDraft(),
)

const comparisonRows = computed(() => [
  {
    label: 'Método',
    expected: contract.value.method,
    actual: requestMethod.value.trim().toUpperCase() || '—',
    matched: requestMethod.value.trim().toUpperCase() === contract.value.method,
  },
  {
    label: 'Path',
    expected: contract.value.path,
    actual: requestPath.value.trim() || '—',
    matched: requestPath.value.trim() === contract.value.path,
  },
  {
    label: 'Status',
    expected: String(contract.value.expectedStatus),
    actual: validationReady.value ? observedStatus.value.trim() || '—' : 'Aguardando execução',
    matched: validationReady.value && observedStatus.value.trim() === String(contract.value.expectedStatus),
  },
  {
    label: 'Headers',
    expected: contract.value.expectedHeaders.join(' | ') || '—',
    actual: validationReady.value ? observedHeaders.value.trim() || '—' : 'Aguardando execução',
    matched: validationReady.value && observedHeaders.value.trim() === contract.value.expectedHeaders.join('\n'),
  },
  {
    label: 'Body',
    expected: contract.value.expectedBody || '—',
    actual: validationReady.value ? observedBody.value.trim() || '—' : 'Aguardando execução',
    matched: validationReady.value && observedBody.value.trim() === contract.value.expectedBody.trim(),
  },
])

const validationSummary = computed(() => {
  if (!validationReady.value) return 'Ajuste a requisição e execute a validação para ver o contraste esperado vs observado.'

  const mismatches = comparisonRows.value.filter((row) => !row.matched)
  if (!mismatches.length) {
    return 'O contrato ficou coerente: método, path, status, headers e body estão alinhados.'
  }

  return `Encontramos ${mismatches.length} divergência(s): ${mismatches.map((row) => row.label.toLowerCase()).join(', ')}.`
})

const requestPreview = computed(() => JSON.stringify({
  method: requestMethod.value.trim().toUpperCase(),
  path: requestPath.value.trim(),
  headers: requestHeaders.value.split('\n').filter(Boolean),
  body: requestBody.value,
}, null, 2))

function runValidation() {
  validationReady.value = true
  const normalizedBody = requestBody.value.trim()
  const matchesMethod = requestMethod.value.trim().toUpperCase() === contract.value.method
  const matchesPath = requestPath.value.trim() === contract.value.path
  const matchesBody = !contract.value.expectedBody || !normalizedBody || normalizedBody === contract.value.expectedBody.trim()

  if (!matchesMethod) {
    observedStatus.value = '405'
    observedHeaders.value = 'Content-Type: application/problem+json'
    observedBody.value = prettyJson({
      error: 'METHOD_NOT_ALLOWED',
      expected: contract.value.method,
      received: requestMethod.value.trim().toUpperCase() || '—',
    })
    return
  }

  if (!matchesPath) {
    observedStatus.value = '404'
    observedHeaders.value = 'Content-Type: application/problem+json'
    observedBody.value = prettyJson({
      error: 'NOT_FOUND',
      expected: contract.value.path,
      received: requestPath.value.trim() || '—',
    })
    return
  }

  if (!matchesBody) {
    observedStatus.value = '422'
    observedHeaders.value = 'Content-Type: application/problem+json'
    observedBody.value = prettyJson({
      error: 'UNPROCESSABLE_ENTITY',
      detail: 'O corpo da requisição não atende ao contrato esperado.',
      expected: contract.value.expectedBody,
      received: normalizedBody || '—',
    })
    return
  }

  observedStatus.value = String(contract.value.expectedStatus)
  observedHeaders.value = contract.value.expectedHeaders.join('\n')
  observedBody.value = contract.value.expectedBody
}

function clearValidation() {
  validationReady.value = false
  observedStatus.value = ''
  observedHeaders.value = ''
  observedBody.value = ''
}

watch(
  () => [requestMethod.value, requestPath.value, requestHeaders.value, requestBody.value],
  () => {
    if (validationReady.value) {
      clearValidation()
    }
  },
)
</script>

<template>
  <Card class="http-contract-shell">
    <CardHeader class="http-contract-shell__header">
      <div class="http-contract-shell__header-copy">
        <p class="eyebrow">{{ config.label }}</p>
        <CardTitle>{{ contract.title }}</CardTitle>
        <CardDescription>
          {{ requestMethod }} {{ requestPath }} · esperado {{ contract.expectedStatus }} · schema {{ contract.responseSchema }}
        </CardDescription>
      </div>
      <div class="http-contract-shell__badges">
        <Badge>{{ requestMethod || contract.method }}</Badge>
        <Badge variant="outline">{{ requestPath || contract.path }}</Badge>
        <Badge variant="outline">{{ contract.expectedStatus }} esperado</Badge>
        <Badge variant="outline">{{ validationReady ? 'Validação pronta' : 'Aguardando execução' }}</Badge>
      </div>
    </CardHeader>

    <CardContent class="http-contract-shell__content">
      <div class="http-contract-shell__summary">
        <div class="http-contract-shell__summary-card">
          <p class="section-label">Resumo do contrato</p>
          <strong>{{ validationSummary }}</strong>
          <p>
            A tela está pronta para receber `workspace_spec` com método, path, status, headers, body e schema de forma canônica.
          </p>
        </div>
        <div class="http-contract-shell__summary-card http-contract-shell__summary-card--accent">
          <p class="section-label">Regra de comparação</p>
          <ul>
            <li v-for="rule in contract.validationRules" :key="rule">{{ rule }}</li>
          </ul>
        </div>
      </div>

      <div class="http-contract-shell__grid">
        <section class="http-contract-panel">
          <p class="section-label">Contrato esperado</p>
          <div class="http-contract-kv">
            <div>
              <span>Método</span>
              <strong>{{ contract.method }}</strong>
            </div>
            <div>
              <span>Path</span>
              <strong>{{ contract.path }}</strong>
            </div>
            <div>
              <span>Status</span>
              <strong>{{ contract.expectedStatus }}</strong>
            </div>
            <div>
              <span>Schema</span>
              <strong>{{ contract.responseSchema }}</strong>
            </div>
          </div>

          <div class="http-contract-stack">
            <div>
              <p class="section-label">Headers esperados</p>
              <div class="http-contract-pill-list">
                <Badge v-for="header in contract.expectedHeaders" :key="header" variant="outline">{{ header }}</Badge>
              </div>
            </div>
            <div>
              <p class="section-label">Body esperado</p>
              <Textarea :model-value="contract.expectedBody" class="http-contract-textarea" :disabled="true" />
            </div>
          </div>
        </section>

        <section class="http-contract-panel">
          <p class="section-label">Requisição em teste</p>
          <div class="http-contract-form">
            <div class="http-contract-form__row">
              <label>
                <span>Método</span>
                <Input v-model="requestMethod" :disabled="readOnly" placeholder="POST" />
              </label>
              <label>
                <span>Path</span>
                <Input v-model="requestPath" :disabled="readOnly" placeholder="/api/contrato" />
              </label>
            </div>

            <label>
              <span>Headers</span>
              <Textarea
                v-model="requestHeaders"
                class="http-contract-textarea"
                :disabled="readOnly"
                placeholder="Content-Type: application/json"
              />
            </label>

            <label>
              <span>Body</span>
              <Textarea
                v-model="requestBody"
                class="http-contract-textarea http-contract-textarea--body"
                :disabled="readOnly"
                placeholder="{&quot;resource&quot;:&quot;logic-arena&quot;}"
              />
            </label>
          </div>
          <div class="http-contract-preview">
            <p class="section-label">Preview serializado</p>
            <code>{{ requestPreview }}</code>
          </div>
        </section>
      </div>

      <div class="http-contract-shell__comparison">
        <Card class="http-contract-card">
          <CardHeader>
            <CardTitle>Comparação lado a lado</CardTitle>
            <CardDescription>Os campos observados são calculados a partir do probe local da requisição.</CardDescription>
          </CardHeader>
          <CardContent class="http-contract-comparison-grid">
            <article v-for="row in comparisonRows" :key="row.label" class="http-contract-comparison-row" :data-matched="row.matched">
              <div class="http-contract-comparison-row__heading">
                <strong>{{ row.label }}</strong>
                <Badge :variant="row.matched ? 'default' : 'outline'">
                  {{ row.matched ? 'Compatível' : 'Divergente' }}
                </Badge>
              </div>
              <div class="http-contract-comparison-row__grid">
                <div>
                  <p class="section-label">Esperado</p>
                  <code>{{ row.expected }}</code>
                </div>
                <div>
                  <p class="section-label">Observado</p>
                  <code>{{ row.actual }}</code>
                </div>
              </div>
            </article>
          </CardContent>
        </Card>

        <Card class="http-contract-card">
          <CardHeader>
            <CardTitle>Resposta observada</CardTitle>
            <CardDescription>
              {{ validationReady ? 'Resultado do probe local e divergências encontradas.' : 'Execute a validação para materializar a resposta observada.' }}
            </CardDescription>
          </CardHeader>
          <CardContent class="http-contract-response">
            <div class="http-contract-response__badges">
              <Badge>{{ validationReady ? `HTTP ${observedStatus || contract.expectedStatus}` : 'Aguardando execução' }}</Badge>
              <Badge variant="outline">{{ validationReady ? 'Resposta materializada' : 'Resposta ainda vazia' }}</Badge>
            </div>

            <div class="http-contract-stack">
              <div>
                <p class="section-label">Headers observados</p>
                <Textarea
                  v-model="observedHeaders"
                  class="http-contract-textarea"
                  :disabled="readOnly"
                  placeholder="Content-Type: application/problem+json"
                />
              </div>
              <div>
                <p class="section-label">Body observado</p>
                <Textarea
                  v-model="observedBody"
                  class="http-contract-textarea http-contract-textarea--body"
                  :disabled="readOnly"
                  placeholder="Resultado observado da resposta"
                />
              </div>
            </div>

            <div class="http-contract-response__status">
              <div>
                <span>Expected vs observed</span>
                <strong>{{ contract.expectedStatus }} → {{ validationReady ? observedStatus || '—' : '—' }}</strong>
              </div>
              <div>
                <span>Checklist</span>
                <ul>
                  <li v-for="hint in contract.comparisonHints" :key="hint">{{ hint }}</li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div class="http-contract-shell__actions">
        <Button variant="outline" :disabled="readOnly" @click="runValidation">
          Executar requisição
        </Button>
        <Button variant="outline" :disabled="readOnly" @click="runValidation">
          Validar contrato
        </Button>
        <Button :disabled="readOnly" @click="runValidation">
          Submeter
        </Button>
      </div>
    </CardContent>
  </Card>
</template>

<style scoped>
.http-contract-shell {
  display: grid;
  gap: 1rem;
}

.http-contract-shell__header {
  display: grid;
  gap: 1rem;
  align-items: start;
}

.http-contract-shell__header-copy {
  display: grid;
  gap: 0.35rem;
}

.http-contract-shell__badges,
.http-contract-response__badges {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.http-contract-shell__content {
  display: grid;
  gap: 1rem;
}

.http-contract-shell__summary {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1rem;
}

.http-contract-shell__summary-card,
.http-contract-panel,
.http-contract-card {
  border: 2px solid var(--on-surface);
  background: var(--surface);
  box-shadow: 4px 4px 0 var(--on-surface);
}

.http-contract-shell__summary-card,
.http-contract-panel {
  padding: 1rem;
}

.http-contract-shell__summary-card--accent {
  background: color-mix(in srgb, var(--primary) 8%, var(--surface));
}

.http-contract-shell__grid {
  display: grid;
  grid-template-columns: 1.05fr 1fr;
  gap: 1rem;
}

.http-contract-kv {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.75rem;
  margin-top: 0.85rem;
}

.http-contract-kv > div,
.http-contract-response__status > div {
  display: grid;
  gap: 0.2rem;
  padding: 0.75rem;
  border: 1px solid var(--on-surface);
  background: var(--surface-low);
}

.http-contract-kv span,
.http-contract-response__status span {
  font-size: 0.68rem;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--on-surface-variant);
}

.http-contract-stack {
  display: grid;
  gap: 0.75rem;
  margin-top: 1rem;
}

.http-contract-pill-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.http-contract-form {
  display: grid;
  gap: 0.85rem;
  margin-top: 0.85rem;
}

.http-contract-form__row {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.75rem;
}

.http-contract-form label {
  display: grid;
  gap: 0.35rem;
}

.http-contract-form label span {
  font-size: 0.68rem;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--on-surface-variant);
}

.http-contract-textarea,
.http-contract-textarea--body {
  min-height: 7rem;
}

.http-contract-preview {
  margin-top: 0.85rem;
  display: grid;
  gap: 0.35rem;
}

.http-contract-preview code {
  white-space: pre-wrap;
  word-break: break-word;
}

.http-contract-shell__comparison {
  display: grid;
  grid-template-columns: 1.08fr 0.92fr;
  gap: 1rem;
}

.http-contract-card {
  display: grid;
}

.http-contract-comparison-grid {
  display: grid;
  gap: 0.9rem;
}

.http-contract-comparison-row {
  display: grid;
  gap: 0.6rem;
  padding: 0.9rem;
  border: 1px solid var(--on-surface);
  background: var(--surface-low);
}

.http-contract-comparison-row[data-matched='true'] {
  background: color-mix(in srgb, #2f9e44 10%, var(--surface-low));
}

.http-contract-comparison-row__heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}

.http-contract-comparison-row__grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.75rem;
}

.http-contract-response {
  display: grid;
  gap: 0.85rem;
}

.http-contract-response__status {
  display: grid;
  gap: 0.75rem;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.http-contract-shell__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  justify-content: flex-end;
}

@media (max-width: 1100px) {
  .http-contract-shell__summary,
  .http-contract-shell__grid,
  .http-contract-shell__comparison,
  .http-contract-kv,
  .http-contract-form__row,
  .http-contract-response__status,
  .http-contract-comparison-row__grid {
    grid-template-columns: 1fr;
  }
}
</style>
