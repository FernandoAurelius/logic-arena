<script setup lang="ts">
import { computed } from 'vue'
import {
  AlertTriangle,
  BadgeCheck,
  Binary,
  Circle,
  Gauge,
  Sparkles,
} from 'lucide-vue-next'

import type { SessionConfig } from '@/entities/practice-session'
import { Badge } from '@/shared/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/shared/ui/card'
import MonacoEditor from '@/shared/ui/editor/MonacoEditor.vue'

import {
  formatAttemptMode,
  getObjectiveContextTags,
  getObjectiveLearningObjectives,
  getObjectiveOptions,
  getObjectiveSelectedOptionDetails,
  getObjectiveSnippet,
  getObjectiveStatement,
  getObjectiveTemplateInfo,
  getObjectiveTemplateMeta,
  toggleObjectiveSelection,
} from './objectiveSurfaceShared'

const selectedOptions = defineModel<string[]>('selectedOptions', { default: [] })
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

const options = computed(() => getObjectiveOptions(props.sessionConfig))
const snippet = computed(() => getObjectiveSnippet(props.sessionConfig))
const objectiveInfo = computed(() => getObjectiveTemplateInfo(props.sessionConfig))
const templateMeta = computed(() => getObjectiveTemplateMeta(props.sessionConfig))
const objectiveStatement = computed(() => getObjectiveStatement(props.sessionConfig))
const learningObjectives = computed(() => getObjectiveLearningObjectives(props.sessionConfig))
const contextTags = computed(() => getObjectiveContextTags(props.sessionConfig))
const selectedDetails = computed(() => getObjectiveSelectedOptionDetails(props.sessionConfig, selectedOptions.value))
const selectedLabels = computed(() => selectedDetails.value.map((option) => option.label))
const selectedMisconceptions = computed(() =>
  selectedDetails.value
    .map((option) => option.misconception_tag)
    .filter((tag): tag is string => Boolean(tag)),
)
const modeLabel = computed(() => formatAttemptMode(props.sessionConfig?.mode))
const templateLabel = computed(() => {
  if (snippet.value.template === 'compile-runtime-output') return 'Compile / Runtime / Output'
  if (snippet.value.template === 'behavior-classification') return 'Behavior classification'
  if (snippet.value.template === 'snippet-read-only') return 'Snippet read-only'
  return objectiveInfo.value.badge
})
const expectsOutputText = computed(() => Boolean(templateMeta.value.requires_output_text))
const selectedLabel = computed(() => selectedLabels.value[0] ?? '')
const analysisSteps = computed(() => templateMeta.value.analysis_steps ?? [])
const responseInputLabel = computed(() => templateMeta.value.response_input_label || 'Saída esperada')
const responseInputPlaceholder = computed(() => templateMeta.value.response_input_placeholder || 'INSIRA A SAÍDA ESPERADA...')

function iconForOption(key: string) {
  const normalized = key.toLowerCase()
  if (normalized.includes('compile')) return AlertTriangle
  if (normalized.includes('runtime')) return Gauge
  if (normalized.includes('output')) return Binary
  return Circle
}

function selectOption(key: string) {
  if (props.readOnly) return
  selectedOptions.value = toggleObjectiveSelection(selectedOptions.value, key, false)
}
</script>

<template>
  <div class="classifier-surface">
    <Card class="classifier-surface__hero">
      <CardHeader class="classifier-surface__hero-header">
        <div class="classifier-surface__hero-copy">
          <p class="eyebrow">Fase 3 · objective_item</p>
          <CardTitle class="classifier-surface__hero-title">{{ props.exerciseTitle }}</CardTitle>
          <CardDescription class="classifier-surface__hero-description">
            {{ objectiveInfo.subtitle }}
            {{ objectiveStatement }}
          </CardDescription>
          <div class="classifier-surface__hero-pills">
            <Badge>{{ templateLabel }}</Badge>
            <Badge variant="outline">{{ modeLabel }}</Badge>
            <Badge variant="outline">{{ expectsOutputText ? 'saida textual' : 'classificação única' }}</Badge>
            <Badge variant="outline">{{ props.sessionConfig?.surface_key ?? 'objective_classifier' }}</Badge>
          </div>
        </div>
        <div class="classifier-surface__hero-metrics">
          <div class="classifier-metric">
            <span class="classifier-metric__label">Conceito-alvo</span>
            <strong>{{ learningObjectives[0] }}</strong>
          </div>
          <div class="classifier-metric">
            <span class="classifier-metric__label">Contexto</span>
            <strong>{{ contextTags.join(' · ') || 'diagnóstico técnico' }}</strong>
          </div>
          <div class="classifier-metric">
            <span class="classifier-metric__label">Snippet</span>
            <strong>{{ snippet.readOnly ? 'read-only' : 'open' }}</strong>
          </div>
          <div class="classifier-metric">
            <span class="classifier-metric__label">Selecionada</span>
            <strong>{{ selectedOptions.length }}</strong>
          </div>
        </div>
      </CardHeader>
    </Card>

    <div class="classifier-surface__layout">
      <aside class="classifier-surface__aside">
        <Card class="classifier-card classifier-card--featured">
          <CardHeader>
            <p class="eyebrow">Diagnóstico exam-like</p>
            <CardTitle>{{ objectiveInfo.lens_title }}</CardTitle>
            <CardDescription>{{ objectiveInfo.subtitle }}</CardDescription>
          </CardHeader>
          <CardContent>
            <p class="classifier-copy">{{ objectiveInfo.lens_copy }}</p>
            <ol v-if="analysisSteps.length" class="classifier-analysis-steps">
              <li v-for="step in analysisSteps" :key="step">{{ step }}</li>
            </ol>
          </CardContent>
        </Card>

        <Card class="classifier-card">
          <CardHeader>
            <p class="eyebrow">Conceitos-alvo</p>
            <CardTitle>O que a leitura mede</CardTitle>
          </CardHeader>
          <CardContent>
            <div class="classifier-badge-cloud">
              <Badge v-for="item in learningObjectives" :key="item" variant="outline">{{ item }}</Badge>
            </div>
          </CardContent>
        </Card>

        <Card class="classifier-card classifier-card--dark">
          <CardHeader>
            <p class="eyebrow">Template ancorado</p>
            <CardTitle>{{ objectiveInfo.action_title }}</CardTitle>
          </CardHeader>
          <CardContent>
            <p class="classifier-copy classifier-copy--inverse">{{ objectiveInfo.action_copy }}</p>
            <div class="classifier-mini-stats">
              <div>
                <span class="classifier-mini-stats__label">Surface</span>
                <strong>{{ props.sessionConfig?.surface_key ?? 'objective_classifier' }}</strong>
              </div>
              <div>
                <span class="classifier-mini-stats__label">Template</span>
                <strong>{{ templateLabel }}</strong>
              </div>
            </div>
          </CardContent>
        </Card>
      </aside>

      <section class="classifier-surface__main">
        <Card class="classifier-frame">
          <div class="classifier-frame__chrome">
            <div class="classifier-frame__lights">
              <span class="classifier-frame__light"></span>
              <span class="classifier-frame__light"></span>
              <span class="classifier-frame__light"></span>
            </div>
            <div class="classifier-frame__title">
              {{ snippet.title.toUpperCase() }} | {{ snippet.lineCount }} LINES
            </div>
            <Badge variant="outline">{{ templateLabel }}</Badge>
          </div>
          <CardContent class="classifier-frame__content">
            <MonacoEditor
              :model-value="snippet.code"
              :language="snippet.language"
              height="24rem"
              :read-only="true"
            />
          </CardContent>
          <div class="classifier-frame__footer">
            <div class="classifier-frame__footer-copy">
              <BadgeCheck :size="16" />
              <span>{{ objectiveInfo.review_copy }}</span>
            </div>
            <div class="classifier-frame__footer-copy classifier-frame__footer-copy--muted">
              <Sparkles :size="16" />
              <span>{{ snippet.readOnly ? 'o snippet é somente leitura e o veredito depende da regra da linguagem' : 'a superfície segue o mesmo contrato, mas em modo editável' }}</span>
            </div>
          </div>
        </Card>
      </section>

      <aside class="classifier-surface__toolbox">
        <Card class="classifier-card classifier-card--tool">
          <CardHeader>
            <p class="eyebrow">Classificador</p>
            <CardTitle>Veredito objetivo</CardTitle>
            <CardDescription>
              Escolha exatamente uma classificação para esta execução.
            </CardDescription>
          </CardHeader>
          <CardContent class="classifier-surface__options">
            <button
              v-for="option in options"
              :key="option.canonical_key ?? option.key"
              class="classifier-option"
              :class="{ 'classifier-option--selected': selectedOptions.includes(option.canonical_key ?? option.key) }"
              type="button"
              :disabled="props.readOnly"
              :aria-pressed="selectedOptions.includes(option.canonical_key ?? option.key)"
              @click="selectOption(option.canonical_key ?? option.key)"
            >
              <component :is="iconForOption(option.canonical_key ?? option.key)" :size="18" />
              <div class="classifier-option__body">
                <strong>{{ option.label }}</strong>
              </div>
            </button>

            <div v-if="expectsOutputText" class="classifier-output">
              <p class="classifier-output__label">{{ responseInputLabel }}</p>
              <input
                v-model="responseText"
                class="classifier-output__input"
                type="text"
                :placeholder="responseInputPlaceholder"
                :disabled="props.readOnly"
              />
            </div>
          </CardContent>
        </Card>

        <Card class="classifier-card classifier-card--analysis">
          <CardHeader>
            <p class="eyebrow">AI mentor</p>
            <CardTitle>{{ objectiveInfo.review_title }}</CardTitle>
          </CardHeader>
          <CardContent>
            <p class="classifier-copy">{{ objectiveInfo.review_copy }}</p>
            <div class="classifier-analysis">
              <div>
                <span class="classifier-mini-stats__label">Selecionada</span>
                <strong>{{ selectedLabel || 'aguardando resposta' }}</strong>
              </div>
              <div>
                <span class="classifier-mini-stats__label">Modo</span>
                <strong>{{ modeLabel }}</strong>
              </div>
            </div>
            <div v-if="selectedMisconceptions.length" class="classifier-analysis__chips">
              <Badge v-for="item in selectedMisconceptions" :key="item" variant="outline">{{ item }}</Badge>
            </div>
          </CardContent>
        </Card>
      </aside>
    </div>
  </div>
</template>

<style scoped>
.classifier-surface {
  display: grid;
  gap: 1rem;
  min-height: 0;
}

.classifier-surface__hero {
  overflow: hidden;
}

.classifier-surface__hero-header {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 1rem;
  align-items: stretch;
}

.classifier-surface__hero-copy {
  display: grid;
  gap: 0.8rem;
}

.classifier-surface__hero-title {
  font-size: clamp(2rem, 3vw, 3.6rem);
  line-height: 0.92;
  letter-spacing: -0.08em;
  text-transform: uppercase;
}

.classifier-surface__hero-description {
  max-width: 54rem;
  line-height: 1.55;
}

.classifier-surface__hero-pills {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.classifier-surface__hero-metrics {
  display: grid;
  grid-template-columns: repeat(2, minmax(8.8rem, 1fr));
  gap: 0.75rem;
  align-self: start;
}

.classifier-metric {
  display: grid;
  gap: 0.3rem;
  padding: 0.85rem 0.95rem;
  border: 2px solid var(--on-surface);
  background: color-mix(in srgb, var(--surface-container) 82%, var(--primary) 18%);
  box-shadow: 4px 4px 0 0 var(--on-surface);
}

.classifier-metric__label {
  font-size: 0.68rem;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.16em;
  color: var(--on-surface-variant);
}

.classifier-metric strong {
  font-size: 0.96rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.classifier-surface__layout {
  display: grid;
  grid-template-columns: minmax(17rem, 22rem) minmax(0, 1fr) minmax(18rem, 21rem);
  gap: 1rem;
  min-height: 0;
  align-items: start;
}

.classifier-surface__aside,
.classifier-surface__main,
.classifier-surface__toolbox {
  display: grid;
  gap: 1rem;
  min-height: 0;
}

.classifier-card {
  overflow: hidden;
  border: 2px solid var(--on-surface);
  box-shadow: 4px 4px 0 0 var(--on-surface);
  background: color-mix(in srgb, var(--surface) 94%, var(--primary) 6%);
}

.classifier-card--featured {
  background: color-mix(in srgb, var(--surface) 88%, var(--primary-container) 12%);
}

.classifier-card--dark {
  background: var(--on-surface);
  color: var(--surface);
  box-shadow: 4px 4px 0 0 color-mix(in srgb, var(--primary) 72%, var(--on-surface));
}

.classifier-card--tool {
  background: color-mix(in srgb, var(--surface) 96%, var(--primary) 4%);
}

.classifier-card--analysis {
  background: color-mix(in srgb, var(--surface) 88%, #dff2e0 12%);
  border-color: #2f9e44;
  box-shadow: 4px 4px 0 0 color-mix(in srgb, #2f9e44 75%, var(--on-surface));
}

.classifier-copy {
  margin: 0;
  line-height: 1.55;
}

.classifier-copy--inverse {
  color: color-mix(in srgb, var(--surface) 92%, white 8%);
}

.classifier-badge-cloud,
.classifier-analysis__chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.classifier-mini-stats,
.classifier-analysis {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.75rem;
  margin-top: 0.95rem;
}

.classifier-mini-stats > div,
.classifier-analysis > div {
  display: grid;
  gap: 0.25rem;
}

.classifier-mini-stats__label {
  font-size: 0.65rem;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: color-mix(in srgb, currentColor 68%, transparent);
}

.classifier-frame {
  display: grid;
  gap: 0;
  overflow: hidden;
}

.classifier-frame__chrome {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0.75rem 0.95rem;
  border-bottom: 2px solid var(--on-surface);
  background: color-mix(in srgb, var(--surface-container) 94%, var(--surface));
}

.classifier-frame__lights {
  display: flex;
  gap: 0.35rem;
}

.classifier-frame__light {
  width: 0.72rem;
  height: 0.72rem;
  border: 2px solid var(--on-surface);
  background: color-mix(in srgb, var(--surface-container-high) 70%, var(--primary) 30%);
}

.classifier-frame__title {
  font-size: 0.72rem;
  font-weight: 800;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: var(--on-surface-variant);
  text-align: center;
  flex: 1;
}

.classifier-frame__content {
  padding: 0;
}

.classifier-frame__footer {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 0.75rem;
  align-items: center;
  padding: 0.8rem 0.95rem;
  border-top: 2px solid var(--on-surface);
  background: color-mix(in srgb, var(--surface-container) 92%, var(--primary) 8%);
}

.classifier-frame__footer-copy {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  font-size: 0.8rem;
  font-weight: 600;
}

.classifier-frame__footer-copy--muted {
  color: var(--on-surface-variant);
}

.classifier-surface__options {
  display: grid;
  gap: 0.8rem;
}

.classifier-analysis-steps {
  margin: 0.9rem 0 0;
  padding-left: 1.1rem;
  display: grid;
  gap: 0.45rem;
  font-size: 0.88rem;
  color: var(--on-surface-variant);
}

.classifier-option {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 0.8rem;
  align-items: start;
  padding: 1rem 1.05rem;
  text-align: left;
  border: 2px solid var(--on-surface);
  background: color-mix(in srgb, var(--surface) 93%, var(--primary) 7%);
  box-shadow: 4px 4px 0 0 var(--on-surface);
  transition:
    transform 140ms ease,
    box-shadow 140ms ease,
    background 140ms ease,
    border-color 140ms ease;
}

.classifier-option:hover:not(:disabled) {
  transform: translate(2px, 2px);
  box-shadow: 2px 2px 0 0 var(--on-surface);
}

.classifier-option--selected {
  border-color: var(--primary);
  background: color-mix(in srgb, var(--surface) 86%, var(--primary-container) 14%);
  box-shadow: 4px 4px 0 0 var(--primary);
}

.classifier-option__body {
  display: grid;
  gap: 0.35rem;
}

.classifier-option__body small {
  line-height: 1.45;
  color: var(--on-surface-variant);
}

.classifier-output {
  display: grid;
  gap: 0.45rem;
  padding: 0.95rem 1rem;
  border: 2px dashed color-mix(in srgb, var(--on-surface) 70%, transparent);
  background: color-mix(in srgb, var(--surface) 88%, var(--primary-container) 12%);
}

.classifier-output__label {
  margin: 0;
  font-size: 0.68rem;
  font-weight: 800;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: var(--on-surface-variant);
}

.classifier-output__input {
  width: 100%;
  min-height: 2.75rem;
  border: 2px solid var(--on-surface);
  background: var(--surface-container-lowest);
  padding: 0.65rem 0.85rem;
  font: inherit;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  outline: none;
}

.classifier-output__input::placeholder {
  color: color-mix(in srgb, var(--on-surface-variant) 65%, transparent);
}

@media (max-width: 1360px) {
  .classifier-surface__layout {
    grid-template-columns: minmax(17rem, 20rem) minmax(0, 1fr);
  }

  .classifier-surface__toolbox {
    grid-column: 1 / -1;
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 1120px) {
  .classifier-surface__hero-header,
  .classifier-surface__layout,
  .classifier-surface__toolbox {
    grid-template-columns: 1fr;
  }

  .classifier-surface__hero-metrics {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .classifier-surface__aside,
  .classifier-surface__main,
  .classifier-surface__toolbox {
    grid-column: auto;
  }
}

@media (max-width: 760px) {
  .classifier-surface__hero-metrics,
  .classifier-mini-stats,
  .classifier-analysis {
    grid-template-columns: 1fr;
  }
}
</style>
