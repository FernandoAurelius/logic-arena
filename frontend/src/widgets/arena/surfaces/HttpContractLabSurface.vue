<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { ArrowRightLeft, BadgeCheck, Radar, Route, ShieldCheck } from 'lucide-vue-next'

import type { SessionConfig } from '@/entities/practice-session'
import { Badge } from '@/shared/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/shared/ui/card'
import { Input } from '@/shared/ui/input'
import { Textarea } from '@/shared/ui/textarea'

const responseText = defineModel<string>('responseText', { default: '' })

const props = withDefaults(defineProps<{
  readOnly?: boolean
  exerciseTitle?: string
  sessionConfig?: SessionConfig | null
}>(), {
  readOnly: false,
  exerciseTitle: 'atividade',
  sessionConfig: null,
})

function asRecord(value: unknown): Record<string, unknown> | null {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return null
  return value as Record<string, unknown>
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
    return JSON.stringify(value, null, 2)
  }
  return fallback
}

function serializeHeaders(value: unknown): string {
  const record = asRecord(value)
  if (!record) return ''
  return Object.entries(record)
    .map(([key, item]) => `${key}: ${String(item)}`)
    .join('\n')
}

function parseHeaders(value: string): Record<string, string> {
  return Object.fromEntries(
    value
      .split('\n')
      .map((line) => line.trim())
      .filter(Boolean)
      .map((line) => {
        const [key, ...rest] = line.split(':')
        return [key.trim().toLowerCase(), rest.join(':').trim()]
      })
      .filter(([key]) => Boolean(key)),
  )
}

const workspaceSpec = computed(() => (props.sessionConfig?.workspace_spec ?? {}) as Record<string, unknown>)
const contract = computed(() => asRecord(workspaceSpec.value.contract) ?? {})
const requestSpec = computed(() => asRecord(contract.value.request) ?? {})
const responseSpec = computed(() => asRecord(contract.value.response) ?? {})
const templateMeta = computed(() => asRecord(workspaceSpec.value.template_meta) ?? {})
const evaluationPlan = computed(() => (props.sessionConfig?.exercise?.evaluation_plan ?? {}) as Record<string, unknown>)

const requestMethod = ref('')
const requestPath = ref('')
const requestHeaders = ref('')
const requestBody = ref('')
const observedStatus = ref('')
const observedHeaders = ref('')
const observedBody = ref('')
const hydrating = ref(false)

function hydrateFromContractPayload() {
  hydrating.value = true
  requestMethod.value = String(requestSpec.value.method ?? 'GET').toUpperCase()
  requestPath.value = String(requestSpec.value.path ?? '/')
  requestHeaders.value = serializeHeaders(requestSpec.value.headers)
  requestBody.value = prettyJson(requestSpec.value.body, '')
  observedStatus.value = ''
  observedHeaders.value = ''
  observedBody.value = ''

  if (responseText.value.trim()) {
    try {
      const parsed = JSON.parse(responseText.value) as Record<string, unknown>
      const request = asRecord(parsed.request) ?? parsed
      const observed = asRecord(parsed.observed_response) ?? parsed
      requestMethod.value = String(request.request_method ?? request.method ?? requestMethod.value).toUpperCase()
      requestPath.value = String(request.request_path ?? request.path ?? requestPath.value)
      requestHeaders.value = serializeHeaders(request.request_headers ?? request.headers) || requestHeaders.value
      requestBody.value = prettyJson(request.request_body ?? request.body, requestBody.value)
      observedStatus.value = String(observed.response_status ?? observed.status ?? '')
      observedHeaders.value = serializeHeaders(observed.response_headers ?? observed.headers)
      observedBody.value = prettyJson(observed.response_body ?? observed.body, '')
    } catch {
      // Keep defaults when persisted payload is not valid JSON yet.
    }
  }

  hydrating.value = false
}

function emitSerializedDraft() {
  if (hydrating.value) return
  responseText.value = JSON.stringify(
    {
      request: {
        method: requestMethod.value.trim().toUpperCase(),
        path: requestPath.value.trim(),
        headers: parseHeaders(requestHeaders.value),
        body: prettyJson(requestBody.value, requestBody.value),
      },
      observed_response: {
        status: Number.parseInt(observedStatus.value, 10) || observedStatus.value.trim(),
        headers: parseHeaders(observedHeaders.value),
        body: prettyJson(observedBody.value, observedBody.value),
      },
    },
    null,
    2,
  )
}

watch(
  () => [props.sessionConfig?.workspace_spec, responseText.value],
  () => hydrateFromContractPayload(),
  { immediate: true, deep: true },
)

watch(
  () => [requestMethod.value, requestPath.value, requestHeaders.value, requestBody.value, observedStatus.value, observedHeaders.value, observedBody.value],
  () => emitSerializedDraft(),
)

const expectedStatus = computed(() => String(responseSpec.value.status_code ?? responseSpec.value.status ?? '200'))
const expectedHeaders = computed(() => serializeHeaders(responseSpec.value.headers))
const expectedBody = computed(() => prettyJson(responseSpec.value.body, ''))
const responseSchema = computed(() => prettyJson(responseSpec.value.body_schema ?? responseSpec.value.schema, ''))
const validationAxes = computed(() => {
  const axes = templateMeta.value.validation_axes
  return Array.isArray(axes) ? axes.map((value) => String(value)) : ['response_status', 'response_headers', 'response_body', 'response_schema']
})

const comparisonRows = computed(() => [
  {
    label: 'Método',
    expected: String(requestSpec.value.method ?? 'GET').toUpperCase(),
    observed: requestMethod.value.trim().toUpperCase() || '—',
  },
  {
    label: 'Path',
    expected: String(requestSpec.value.path ?? '/'),
    observed: requestPath.value.trim() || '—',
  },
  {
    label: 'Status',
    expected: expectedStatus.value,
    observed: observedStatus.value.trim() || '—',
  },
])
</script>

<template>
  <div class="http-contract-surface">
    <aside class="http-contract-surface__aside">
      <Card class="http-contract-card http-contract-card--featured">
        <CardHeader>
          <p class="eyebrow">Fase 6 · contract_behavior_lab</p>
          <CardTitle>{{ exerciseTitle }}</CardTitle>
          <CardDescription>
            {{ sessionConfig?.exercise?.statement }}
          </CardDescription>
        </CardHeader>
        <CardContent class="http-contract-card__content">
          <div class="http-contract-badges">
            <Badge>http_contract_lab</Badge>
            <Badge variant="outline">{{ sessionConfig?.mode ?? 'practice' }}</Badge>
            <Badge variant="outline">{{ sessionConfig?.family_key ?? 'contract_behavior_lab' }}</Badge>
          </div>
          <p class="http-contract-copy">
            {{ String(workspaceSpec.instructions ?? evaluationPlan.instructions ?? 'Registre a request e a response observadas antes de validar o contrato.') }}
          </p>
        </CardContent>
      </Card>

      <Card class="http-contract-card">
        <CardHeader>
          <p class="eyebrow">Lentes de análise</p>
          <CardTitle>O que precisa bater</CardTitle>
        </CardHeader>
        <CardContent class="http-contract-card__content">
          <div class="http-contract-badges">
            <Badge v-for="axis in validationAxes" :key="axis" variant="outline">{{ axis }}</Badge>
          </div>
          <ol class="http-contract-steps">
            <li v-for="step in (Array.isArray(templateMeta.analysis_steps) ? templateMeta.analysis_steps : [])" :key="String(step)">
              {{ String(step) }}
            </li>
          </ol>
        </CardContent>
      </Card>
    </aside>

    <section class="http-contract-surface__main">
      <div class="http-contract-grid">
        <Card class="http-contract-frame">
          <CardHeader class="http-contract-frame__header">
            <div>
              <p class="eyebrow">Contrato esperado</p>
              <CardTitle>Request + Response</CardTitle>
            </div>
            <Badge variant="outline">
              <Route :size="12" />
              {{ String(requestSpec.method ?? 'GET').toUpperCase() }} {{ String(requestSpec.path ?? '/') }}
            </Badge>
          </CardHeader>
          <CardContent class="http-contract-frame__content">
            <div class="http-contract-pane">
              <div class="http-contract-pane__section">
                <span class="section-label">Headers esperados</span>
                <pre>{{ serializeHeaders(requestSpec.headers) || 'sem headers obrigatórios' }}</pre>
              </div>
              <div class="http-contract-pane__section">
                <span class="section-label">Body esperado</span>
                <pre>{{ prettyJson(requestSpec.body, 'sem body esperado') }}</pre>
              </div>
            </div>
            <div class="http-contract-pane">
              <div class="http-contract-pane__section">
                <span class="section-label">Status esperado</span>
                <strong>{{ expectedStatus }}</strong>
              </div>
              <div class="http-contract-pane__section">
                <span class="section-label">Headers esperados</span>
                <pre>{{ expectedHeaders || 'sem headers obrigatórios' }}</pre>
              </div>
              <div class="http-contract-pane__section">
                <span class="section-label">Body esperado</span>
                <pre>{{ expectedBody || 'sem body esperado' }}</pre>
              </div>
              <div class="http-contract-pane__section">
                <span class="section-label">Schema</span>
                <pre>{{ responseSchema || 'sem schema declarado' }}</pre>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card class="http-contract-frame">
          <CardHeader class="http-contract-frame__header">
            <div>
              <p class="eyebrow">Observação registrada</p>
              <CardTitle>O que você viu na execução</CardTitle>
            </div>
            <Badge variant="outline">
              <Radar :size="12" />
              pronto para validar
            </Badge>
          </CardHeader>
          <CardContent class="http-contract-form">
            <div class="http-contract-form__row">
              <Input v-model="requestMethod" :disabled="readOnly" placeholder="POST" />
              <Input v-model="requestPath" :disabled="readOnly" placeholder="/api/users" />
            </div>
            <Textarea v-model="requestHeaders" :disabled="readOnly" placeholder="content-type: application/json" class="http-contract-textarea http-contract-textarea--compact" />
            <Textarea v-model="requestBody" :disabled="readOnly" placeholder='{"name":"Miguel"}' class="http-contract-textarea" />
            <div class="http-contract-form__row">
              <Input v-model="observedStatus" :disabled="readOnly" placeholder="201" />
              <Badge variant="outline" class="http-contract-form__pill">
                <BadgeCheck :size="12" />
                response observada
              </Badge>
            </div>
            <Textarea v-model="observedHeaders" :disabled="readOnly" placeholder="content-type: application/json" class="http-contract-textarea http-contract-textarea--compact" />
            <Textarea v-model="observedBody" :disabled="readOnly" placeholder='{"id":1,"name":"Miguel"}' class="http-contract-textarea" />
          </CardContent>
        </Card>
      </div>

      <Card class="http-contract-comparison">
        <CardHeader class="http-contract-frame__header">
          <div>
            <p class="eyebrow">Comparação rápida</p>
            <CardTitle>Esperado vs observado</CardTitle>
          </div>
          <Badge variant="outline">
            <ArrowRightLeft :size="12" />
            contrato
          </Badge>
        </CardHeader>
        <CardContent class="http-contract-comparison__content">
          <div v-for="row in comparisonRows" :key="row.label" class="http-contract-compare-row">
            <strong>{{ row.label }}</strong>
            <div>
              <span class="section-label">Esperado</span>
              <p>{{ row.expected }}</p>
            </div>
            <div>
              <span class="section-label">Observado</span>
              <p>{{ row.observed }}</p>
            </div>
          </div>
          <div class="http-contract-hint">
            <ShieldCheck :size="14" />
            <span>Use a toolbar da Arena para validar ou submeter. Esta superfície só registra a observação do contrato.</span>
          </div>
        </CardContent>
      </Card>
    </section>
  </div>
</template>

<style scoped>
.http-contract-surface {
  display: grid;
  grid-template-columns: 20rem minmax(0, 1fr);
  gap: 1rem;
  min-height: 0;
  height: 100%;
}

.http-contract-surface__aside,
.http-contract-surface__main {
  min-height: 0;
  display: grid;
  gap: 1rem;
}

.http-contract-card,
.http-contract-frame,
.http-contract-comparison {
  min-height: 0;
}

.http-contract-card__content,
.http-contract-comparison__content {
  display: grid;
  gap: 0.9rem;
}

.http-contract-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.http-contract-copy,
.http-contract-steps {
  color: var(--muted);
}

.http-contract-steps {
  padding-left: 1.25rem;
  display: grid;
  gap: 0.45rem;
}

.http-contract-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1rem;
}

.http-contract-frame__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}

.http-contract-frame__content {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1rem;
}

.http-contract-pane,
.http-contract-form {
  display: grid;
  gap: 0.85rem;
}

.http-contract-pane__section {
  display: grid;
  gap: 0.35rem;
  padding: 0.9rem;
  border-radius: 1rem;
  border: 1.5px solid color-mix(in srgb, var(--border) 70%, transparent);
  background: color-mix(in srgb, var(--surface) 92%, var(--primary) 8%);
}

.http-contract-pane__section pre {
  white-space: pre-wrap;
  word-break: break-word;
  color: var(--muted);
  margin: 0;
}

.http-contract-form__row {
  display: grid;
  grid-template-columns: minmax(0, 10rem) minmax(0, 1fr);
  gap: 0.75rem;
  align-items: center;
}

.http-contract-form__pill {
  justify-self: start;
  gap: 0.35rem;
}

.http-contract-textarea {
  min-height: 9rem;
}

.http-contract-textarea--compact {
  min-height: 6rem;
}

.http-contract-compare-row {
  display: grid;
  grid-template-columns: 8rem repeat(2, minmax(0, 1fr));
  gap: 1rem;
  padding: 0.9rem 0;
  border-bottom: 1px solid color-mix(in srgb, var(--border) 50%, transparent);
}

.http-contract-hint {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  color: var(--muted);
}

@media (max-width: 1200px) {
  .http-contract-surface {
    grid-template-columns: 1fr;
  }

  .http-contract-grid,
  .http-contract-frame__content,
  .http-contract-compare-row,
  .http-contract-form__row {
    grid-template-columns: 1fr;
  }
}
</style>
