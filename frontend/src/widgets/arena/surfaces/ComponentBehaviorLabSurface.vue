<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/shared/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/shared/ui/tabs'
import type { SessionConfig } from '@/entities/practice-session'

import CodeWorkspaceSurface from './CodeWorkspaceSurface.vue'

const code = defineModel<string>('code', { default: '' })
const workspaceFiles = defineModel<Record<string, string>>('workspaceFiles', { default: {} })
const activeFile = defineModel<string>('activeFile', { default: '' })
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

type BehaviorVariant = 'default' | 'compact' | 'loading' | 'success'
type BehaviorTab = 'props' | 'estado' | 'eventos' | 'dom'

function asRecord(value: unknown): Record<string, unknown> | null {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return null
  return value as Record<string, unknown>
}

const workspaceSpec = computed(() => (props.sessionConfig?.workspace_spec ?? {}) as Record<string, unknown>)
const componentContract = computed(() => asRecord(workspaceSpec.value.component_contract) ?? {})
const templateMeta = computed(() => asRecord(workspaceSpec.value.template_meta) ?? {})

const variant = ref<BehaviorVariant>('default')
const highlighted = ref(false)
const expanded = ref(true)
const clickCount = ref(0)
const activeTab = ref<BehaviorTab>('props')
const eventLog = ref<string[]>(['render: componente iniciado.'])
const hydrating = ref(false)

const expectedProps = computed(() => Array.isArray(componentContract.value.expected_props) ? componentContract.value.expected_props.map(String) : [])
const expectedState = computed(() => Array.isArray(componentContract.value.expected_state) ? componentContract.value.expected_state.map(String) : [])
const expectedEvents = computed(() => Array.isArray(componentContract.value.expected_events) ? componentContract.value.expected_events.map(String) : [])
const expectedRender = computed(() => Array.isArray(componentContract.value.expected_render) ? componentContract.value.expected_render.map(String) : [])
const expectedDom = computed(() => Array.isArray(componentContract.value.expected_dom) ? componentContract.value.expected_dom.map(String) : [])
const expectedDomSnapshot = computed(() => String(componentContract.value.expected_dom_snapshot ?? ''))

const observedLabel = computed(() => {
  if (variant.value === 'loading') return 'Carregando...'
  if (variant.value === 'success') return 'Concluído'
  if (highlighted.value) return 'Foco ativo'
  return 'Pronto para interação'
})

const propsState = computed(() => [
  { label: 'title', value: props.exerciseTitle || 'ComponentUnderTest' },
  { label: 'variant', value: variant.value },
  { label: 'expanded', value: expanded.value ? 'true' : 'false' },
  { label: 'highlighted', value: highlighted.value ? 'true' : 'false' },
])

const observedDom = computed(() => [
  '<article class="activity-card"',
  `  data-variant="${variant.value}"`,
  `  data-expanded="${expanded.value}"`,
  `  data-highlighted="${highlighted.value}"`,
  '>',
  `  <header>${observedLabel.value}</header>`,
  `  <button type="button">Interações ${clickCount.value}</button>`,
  expanded.value ? '  <p>Painel expandido</p>' : '  <p>Painel recolhido</p>',
  '</article>',
].join('\n'))

function pushEvent(message: string) {
  const timestamp = new Date().toLocaleTimeString('pt-BR', { hour12: false })
  eventLog.value = [`${timestamp} · ${message}`, ...eventLog.value].slice(0, 6)
}

function cycleVariant() {
  if (props.readOnly) return
  const order: BehaviorVariant[] = ['default', 'compact', 'loading', 'success']
  variant.value = order[(order.indexOf(variant.value) + 1) % order.length]
  pushEvent(`variant alterado para ${variant.value}`)
}

function toggleExpanded() {
  if (props.readOnly) return
  expanded.value = !expanded.value
  pushEvent(expanded.value ? 'painel expandido' : 'painel recolhido')
}

function toggleHighlight() {
  if (props.readOnly) return
  highlighted.value = !highlighted.value
  pushEvent(highlighted.value ? 'destaque ativado' : 'destaque removido')
}

function incrementClicks() {
  if (props.readOnly) return
  clickCount.value += 1
  pushEvent('evento click disparado')
}

function resetLab() {
  if (props.readOnly) return
  variant.value = 'default'
  highlighted.value = false
  expanded.value = true
  clickCount.value = 0
  eventLog.value = ['render: componente reiniciado.']
}

function hydrateObservation() {
  hydrating.value = true
  variant.value = 'default'
  highlighted.value = false
  expanded.value = true
  clickCount.value = 0
  eventLog.value = ['render: componente iniciado.']

  if (responseText.value.trim()) {
    try {
      const parsed = JSON.parse(responseText.value) as Record<string, unknown>
      variant.value = ['default', 'compact', 'loading', 'success'].includes(String(parsed.variant))
        ? String(parsed.variant) as BehaviorVariant
        : 'default'
      highlighted.value = Boolean(parsed.highlighted)
      expanded.value = parsed.expanded !== false
      clickCount.value = Number(parsed.click_count ?? 0) || 0
      if (Array.isArray(parsed.event_log)) {
        eventLog.value = parsed.event_log.map(String)
      }
    } catch {
      // keep defaults
    }
  }

  hydrating.value = false
}

function emitObservation() {
  if (hydrating.value) return
  responseText.value = JSON.stringify(
    {
      variant: variant.value,
      highlighted: highlighted.value,
      expanded: expanded.value,
      click_count: clickCount.value,
      observed_state: {
        variant: variant.value,
        highlighted: highlighted.value,
        expanded: expanded.value,
        click_count: clickCount.value,
      },
      observed_dom: observedDom.value,
      event_log: eventLog.value,
    },
    null,
    2,
  )
}

watch(
  () => [props.sessionConfig?.workspace_spec, responseText.value],
  () => hydrateObservation(),
  { immediate: true, deep: true },
)

watch(
  () => [variant.value, highlighted.value, expanded.value, clickCount.value, eventLog.value],
  () => emitObservation(),
  { deep: true },
)
</script>

<template>
  <div class="component-behavior-surface">
    <aside class="component-behavior-surface__aside">
      <Card class="component-behavior-card component-behavior-card--featured">
        <CardHeader>
          <p class="eyebrow">Fase 7 · component_behavior_lab</p>
          <CardTitle>{{ exerciseTitle }}</CardTitle>
          <CardDescription>{{ sessionConfig?.exercise?.statement }}</CardDescription>
        </CardHeader>
        <CardContent class="component-behavior-card__content">
          <div class="component-behavior-badges">
            <Badge>component_behavior_lab</Badge>
            <Badge variant="outline">{{ sessionConfig?.mode ?? 'practice' }}</Badge>
            <Badge variant="outline">{{ sessionConfig?.family_key ?? 'contract_behavior_lab' }}</Badge>
          </div>
          <p class="component-behavior-copy">
            {{ String(workspaceSpec.instructions ?? 'Edite o componente, observe o preview e compare o contrato visual.') }}
          </p>
        </CardContent>
      </Card>

      <Card class="component-behavior-card">
        <CardHeader>
          <p class="eyebrow">Lentes de análise</p>
          <CardTitle>O que precisa bater</CardTitle>
        </CardHeader>
        <CardContent class="component-behavior-card__content">
          <div class="component-behavior-badges">
            <Badge v-for="axis in (Array.isArray(templateMeta.validation_axes) ? templateMeta.validation_axes : [])" :key="String(axis)" variant="outline">
              {{ String(axis) }}
            </Badge>
          </div>
          <ol class="component-behavior-steps">
            <li v-for="step in (Array.isArray(templateMeta.analysis_steps) ? templateMeta.analysis_steps : [])" :key="String(step)">
              {{ String(step) }}
            </li>
          </ol>
        </CardContent>
      </Card>

      <Card class="component-behavior-card">
        <CardHeader>
          <p class="eyebrow">Contrato do componente</p>
          <CardTitle>Checklist esperado</CardTitle>
        </CardHeader>
        <CardContent class="component-behavior-card__content">
          <div class="contract-list">
            <div class="contract-block">
              <span class="section-label">Props</span>
              <p>{{ expectedProps.join(', ') || 'sem props obrigatórias' }}</p>
            </div>
            <div class="contract-block">
              <span class="section-label">Estado</span>
              <p>{{ expectedState.join(', ') || 'sem estado obrigatório' }}</p>
            </div>
            <div class="contract-block">
              <span class="section-label">Eventos</span>
              <p>{{ expectedEvents.join(', ') || 'sem eventos obrigatórios' }}</p>
            </div>
            <div class="contract-block">
              <span class="section-label">Render</span>
              <p>{{ expectedRender.join(', ') || 'sem render obrigatório' }}</p>
            </div>
            <div class="contract-block">
              <span class="section-label">DOM</span>
              <p>{{ expectedDom.join(', ') || 'sem marcadores de DOM' }}</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </aside>

    <section class="component-behavior-surface__main">
      <div class="component-behavior-grid">
        <div class="component-behavior-editor">
          <CodeWorkspaceSurface
            v-model="code"
            v-model:workspace-files="workspaceFiles"
            v-model:active-file="activeFile"
            surface-key="code_editor_single"
            :read-only="readOnly"
            :exercise-title="exerciseTitle"
            :session-config="sessionConfig"
          />
        </div>

        <div class="component-behavior-preview">
          <Card class="component-behavior-frame">
            <CardHeader class="component-behavior-frame__header">
              <div>
                <p class="eyebrow">Preview controlado</p>
                <CardTitle>Estado observável</CardTitle>
                <CardDescription>Simule o comportamento atual do componente antes de validar.</CardDescription>
              </div>
              <Badge variant="outline">{{ observedLabel }}</Badge>
            </CardHeader>
            <CardContent class="component-behavior-frame__content">
              <div class="preview-shell" :data-variant="variant">
                <div class="preview-shell__toolbar">
                  <Button variant="outline" size="sm" :disabled="readOnly" @click="cycleVariant">Trocar variante</Button>
                  <Button variant="outline" size="sm" :disabled="readOnly" @click="toggleHighlight">Alternar foco</Button>
                  <Button variant="outline" size="sm" :disabled="readOnly" @click="toggleExpanded">Expandir/Recolher</Button>
                  <Button size="sm" :disabled="readOnly" @click="incrementClicks">Disparar click</Button>
                </div>

                <article class="preview-card" :data-highlighted="highlighted" :data-expanded="expanded">
                  <div class="preview-card__topline">
                    <Badge variant="outline">activity-card</Badge>
                    <Badge>{{ variant }}</Badge>
                  </div>
                  <header class="preview-card__title">
                    <strong>{{ exerciseTitle }}</strong>
                    <span>{{ observedLabel }}</span>
                  </header>
                  <p class="preview-card__copy">
                    {{ expanded ? 'Painel expandido' : 'Painel recolhido' }}
                  </p>
                  <div class="preview-card__chips">
                    <button class="preview-chip" type="button" :disabled="readOnly" @click="incrementClicks">
                      Interações: {{ clickCount }}
                    </button>
                    <button class="preview-chip preview-chip--ghost" type="button" :disabled="readOnly" @click="resetLab">
                      Resetar
                    </button>
                  </div>
                </article>
              </div>
            </CardContent>
          </Card>

          <Card class="component-behavior-frame">
            <CardHeader class="component-behavior-frame__header">
              <div>
                <p class="eyebrow">Inspector</p>
                <CardTitle>Props, estado, eventos e DOM</CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <Tabs v-model:model-value="activeTab" class="component-behavior-tabs">
                <TabsList class="component-behavior-tabs__list">
                  <TabsTrigger value="props">Props</TabsTrigger>
                  <TabsTrigger value="estado">Estado</TabsTrigger>
                  <TabsTrigger value="eventos">Eventos</TabsTrigger>
                  <TabsTrigger value="dom">DOM</TabsTrigger>
                </TabsList>

                <TabsContent value="props" class="component-behavior-tabs__panel">
                  <div class="kv-grid">
                    <div v-for="item in propsState" :key="item.label" class="kv-row">
                      <span>{{ item.label }}</span>
                      <strong>{{ item.value }}</strong>
                    </div>
                  </div>
                </TabsContent>

                <TabsContent value="estado" class="component-behavior-tabs__panel">
                  <div class="state-grid">
                    <div class="state-pill" :data-active="variant === 'default'">default</div>
                    <div class="state-pill" :data-active="variant === 'compact'">compact</div>
                    <div class="state-pill" :data-active="variant === 'loading'">loading</div>
                    <div class="state-pill" :data-active="variant === 'success'">success</div>
                    <div class="state-pill" :data-active="expanded">expanded</div>
                    <div class="state-pill" :data-active="highlighted">highlighted</div>
                  </div>
                </TabsContent>

                <TabsContent value="eventos" class="component-behavior-tabs__panel">
                  <div class="event-log">
                    <article v-for="entry in eventLog" :key="entry" class="event-log__item">
                      <Badge variant="outline">event</Badge>
                      <span>{{ entry }}</span>
                    </article>
                  </div>
                </TabsContent>

                <TabsContent value="dom" class="component-behavior-tabs__panel">
                  <div class="dom-grid">
                    <article class="dom-card">
                      <p class="section-label">Esperado</p>
                      <pre>{{ expectedDomSnapshot || expectedDom.join('\n') || 'sem DOM esperado explícito' }}</pre>
                    </article>
                    <article class="dom-card dom-card--accent">
                      <p class="section-label">Observado</p>
                      <pre>{{ observedDom }}</pre>
                    </article>
                  </div>
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.component-behavior-surface {
  display: grid;
  grid-template-columns: 20rem minmax(0, 1fr);
  gap: 1rem;
  min-height: 0;
  height: 100%;
}

.component-behavior-surface__aside,
.component-behavior-surface__main {
  min-height: 0;
  display: grid;
  gap: 1rem;
}

.component-behavior-card__content,
.component-behavior-frame__content {
  display: grid;
  gap: 0.9rem;
}

.component-behavior-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.component-behavior-copy,
.component-behavior-steps {
  color: var(--muted);
}

.component-behavior-steps {
  padding-left: 1.25rem;
  display: grid;
  gap: 0.45rem;
}

.contract-list {
  display: grid;
  gap: 0.75rem;
}

.contract-block,
.kv-row,
.event-log__item,
.dom-card {
  display: grid;
  gap: 0.35rem;
  padding: 0.9rem;
  border-radius: 1rem;
  border: 1.5px solid color-mix(in srgb, var(--border) 70%, transparent);
  background: color-mix(in srgb, var(--surface) 92%, var(--primary) 8%);
}

.component-behavior-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.05fr) minmax(22rem, 0.95fr);
  gap: 1rem;
  min-height: 0;
}

.component-behavior-editor,
.component-behavior-preview {
  min-height: 0;
  display: grid;
  gap: 1rem;
}

.component-behavior-frame__header {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: flex-start;
}

.preview-shell {
  display: grid;
  gap: 1rem;
  padding: 1rem;
  border-radius: 1rem;
  border: 1px solid color-mix(in srgb, var(--border) 60%, transparent);
  background: color-mix(in srgb, var(--surface) 90%, var(--accent) 10%);
}

.preview-shell__toolbar,
.preview-card__topline,
.preview-card__chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.preview-card {
  display: grid;
  gap: 0.75rem;
  padding: 1rem;
  border-radius: 1rem;
  border: 1px solid color-mix(in srgb, var(--border) 60%, transparent);
  background: color-mix(in srgb, var(--surface) 94%, var(--card) 6%);
}

.preview-card__title {
  display: flex;
  justify-content: space-between;
  gap: 0.75rem;
}

.preview-card__copy {
  margin: 0;
  color: var(--muted);
}

.preview-chip {
  border: 1px solid color-mix(in srgb, var(--border) 70%, transparent);
  background: color-mix(in srgb, var(--surface) 85%, var(--accent) 15%);
  color: var(--foreground);
  border-radius: 999px;
  padding: 0.55rem 0.8rem;
  font-size: 0.85rem;
  cursor: pointer;
}

.preview-chip--ghost {
  background: color-mix(in srgb, var(--surface) 92%, transparent);
}

.component-behavior-tabs__list {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.component-behavior-tabs__panel {
  min-height: 16rem;
}

.kv-grid,
.state-grid,
.event-log,
.dom-grid {
  display: grid;
  gap: 0.75rem;
}

.state-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.state-pill {
  padding: 0.8rem 0.95rem;
  border-radius: 999px;
  text-align: center;
  border: 1px solid color-mix(in srgb, var(--border) 70%, transparent);
  background: color-mix(in srgb, var(--surface) 90%, transparent);
  color: var(--muted);
}

.state-pill[data-active='true'] {
  border-color: color-mix(in srgb, var(--accent) 55%, transparent);
  background: color-mix(in srgb, var(--accent) 20%, transparent);
  color: var(--foreground);
}

.dom-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.dom-card--accent {
  border-color: color-mix(in srgb, var(--accent) 45%, transparent);
}

.dom-card pre {
  white-space: pre-wrap;
  word-break: break-word;
  margin: 0;
}

@media (max-width: 1400px) {
  .component-behavior-surface,
  .component-behavior-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .component-behavior-tabs__list,
  .state-grid,
  .dom-grid {
    grid-template-columns: 1fr;
  }
}
</style>
