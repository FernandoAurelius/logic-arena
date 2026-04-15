<script setup lang="ts">
import { computed } from 'vue'
import {
  BadgeCheck,
  CheckCircle2,
  Circle,
  Sparkles,
  Timer,
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
  isObjectiveMultiple,
  toggleObjectiveSelection,
} from './objectiveSurfaceShared'

const selectedOptions = defineModel<string[]>('selectedOptions', { default: [] })
defineModel<string>('responseText', { default: '' })

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
const allowMultiple = computed(() => isObjectiveMultiple(props.sessionConfig))
const objectiveInfo = computed(() => getObjectiveTemplateInfo(props.sessionConfig))
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
const difficulty = computed(() => props.sessionConfig?.exercise?.difficulty ?? 'intermediário')
const estimatedTime = computed(() => props.sessionConfig?.exercise?.estimated_time_minutes ?? 10)
const modeLabel = computed(() => formatAttemptMode(props.sessionConfig?.mode))
const snippetTone = computed(() => {
  if (snippet.value.template === 'compile-runtime-output') return 'diagnóstico de execução'
  if (snippet.value.template === 'behavior-classification') return 'comportamento observável'
  if (snippet.value.template === 'snippet-read-only') return 'leitura read-only'
  return allowMultiple.value ? 'discriminação múltipla' : 'resposta única'
})

function toggleOption(key: string) {
  if (props.readOnly) return
  selectedOptions.value = toggleObjectiveSelection(selectedOptions.value, key, allowMultiple.value)
}
</script>

<template>
  <div class="objective-surface">
    <Card class="objective-surface__hero">
      <CardHeader class="objective-surface__hero-header">
        <div class="objective-surface__hero-copy">
          <p class="eyebrow">Fase 2 · objective_item</p>
          <CardTitle class="objective-surface__hero-title">{{ props.exerciseTitle }}</CardTitle>
          <CardDescription class="objective-surface__hero-description">
            {{ objectiveInfo.subtitle }}
            {{ objectiveStatement }}
          </CardDescription>
          <div class="objective-surface__hero-pills">
            <Badge>{{ objectiveInfo.badge }}</Badge>
            <Badge variant="outline">{{ modeLabel }}</Badge>
            <Badge variant="outline">{{ allowMultiple ? 'múltipla resposta' : 'resposta única' }}</Badge>
            <Badge variant="outline">{{ snippet.readOnly ? 'snippet read-only' : 'estímulo aberto' }}</Badge>
          </div>
        </div>
        <div class="objective-surface__hero-metrics">
          <div class="objective-metric">
            <span class="objective-metric__label">Dificuldade</span>
            <strong>{{ difficulty }}</strong>
          </div>
          <div class="objective-metric">
            <span class="objective-metric__label">Tempo</span>
            <strong>{{ estimatedTime }} MIN</strong>
          </div>
          <div class="objective-metric">
            <span class="objective-metric__label">Estímulo</span>
            <strong>{{ snippetTone }}</strong>
          </div>
          <div class="objective-metric">
            <span class="objective-metric__label">Selecionadas</span>
            <strong>{{ selectedOptions.length }}</strong>
          </div>
        </div>
      </CardHeader>
    </Card>

    <div class="objective-surface__layout">
      <aside class="objective-surface__aside">
        <Card class="objective-card objective-card--featured">
          <CardHeader>
            <p class="eyebrow">Objetivo pedagógico</p>
            <CardTitle>{{ objectiveInfo.lens_title }}</CardTitle>
            <CardDescription>{{ objectiveInfo.subtitle }}</CardDescription>
          </CardHeader>
          <CardContent>
            <p class="objective-copy">{{ objectiveStatement }}</p>
          </CardContent>
        </Card>

        <Card class="objective-card">
          <CardHeader>
            <p class="eyebrow">Conceitos-alvo</p>
            <CardTitle>O que precisa ficar claro</CardTitle>
          </CardHeader>
          <CardContent>
            <div class="objective-badge-cloud">
              <Badge v-for="item in learningObjectives" :key="item" variant="outline">{{ item }}</Badge>
            </div>
          </CardContent>
        </Card>

        <Card class="objective-card objective-card--dark">
          <CardHeader>
            <p class="eyebrow">Sinal do template</p>
            <CardTitle>{{ objectiveInfo.action_title }}</CardTitle>
          </CardHeader>
          <CardContent>
            <p class="objective-copy objective-copy--inverse">{{ objectiveInfo.action_copy }}</p>
            <div class="objective-mini-stats">
              <div>
                <span class="objective-mini-stats__label">Surface</span>
                <strong>{{ props.sessionConfig?.surface_key ?? 'objective_choices' }}</strong>
              </div>
              <div>
                <span class="objective-mini-stats__label">Choice mode</span>
                <strong>{{ allowMultiple ? 'multiple' : 'single' }}</strong>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card class="objective-card objective-card--progress">
          <CardHeader>
            <p class="eyebrow">Status da seleção</p>
            <CardTitle>{{ selectedOptions.length }} selecionada(s)</CardTitle>
          </CardHeader>
          <CardContent class="objective-progress">
            <div class="objective-progress__row">
              <span>Alternativas</span>
              <strong>{{ options.length }}</strong>
            </div>
            <div class="objective-progress__row">
              <span>Snippet</span>
              <strong>{{ snippet.readOnly ? 'read-only' : 'editável' }}</strong>
            </div>
            <div class="objective-progress__row">
              <span>Modo</span>
              <strong>{{ modeLabel }}</strong>
            </div>
          </CardContent>
        </Card>
      </aside>

      <section class="objective-surface__main">
        <Card class="objective-frame">
          <div class="objective-frame__chrome">
            <div class="objective-frame__lights">
              <span class="objective-frame__light"></span>
              <span class="objective-frame__light"></span>
              <span class="objective-frame__light"></span>
            </div>
            <div class="objective-frame__title">
              {{ snippet.title.toUpperCase() }} | {{ snippet.lineCount }} LINES
            </div>
            <Badge variant="outline">{{ props.sessionConfig?.surface_key ?? 'objective_choices' }}</Badge>
          </div>
          <CardContent class="objective-frame__content">
            <MonacoEditor
              :model-value="snippet.code"
              :language="snippet.language"
              height="24rem"
              :read-only="true"
            />
          </CardContent>
          <div class="objective-frame__footer">
            <div class="objective-frame__footer-copy">
              <BadgeCheck :size="16" />
              <span>{{ snippet.readOnly ? 'Leitura imutável. A resposta depende da interpretação do estímulo.' : 'Superfície objetiva preparada para leitura e decisão.' }}</span>
            </div>
            <div class="objective-frame__footer-copy objective-frame__footer-copy--muted">
              <Sparkles :size="16" />
              <span>{{ objectiveInfo.review_copy }}</span>
            </div>
          </div>
        </Card>

        <Card class="objective-card objective-card--choices">
          <CardHeader>
            <p class="eyebrow">Alternativas</p>
            <CardTitle>
              {{ allowMultiple ? 'Selecione todas as respostas corretas' : 'Escolha a melhor resposta' }}
            </CardTitle>
            <CardDescription>
              As alternativas foram desenhadas para medir leitura técnica e discriminação conceitual.
            </CardDescription>
          </CardHeader>
          <CardContent class="objective-surface__choices-list">
            <button
              v-for="option in options"
              :key="option.canonical_key ?? option.key"
              class="objective-choice"
              :class="{ 'objective-choice--selected': selectedOptions.includes(option.canonical_key ?? option.key) }"
              type="button"
              :disabled="props.readOnly"
              :aria-pressed="selectedOptions.includes(option.canonical_key ?? option.key)"
              @click="toggleOption(option.canonical_key ?? option.key)"
            >
              <div class="objective-choice__marker">
                <CheckCircle2
                  v-if="selectedOptions.includes(option.canonical_key ?? option.key)"
                  :size="18"
                />
                <Circle v-else :size="18" />
              </div>
              <div class="objective-choice__body">
                <div class="objective-choice__label-row">
                  <strong>{{ option.key.toUpperCase() }}</strong>
                  <Badge
                    v-if="option.misconception_tag"
                    variant="outline"
                  >
                    misconception
                  </Badge>
                </div>
                <p>{{ option.label }}</p>
              </div>
            </button>
          </CardContent>
        </Card>
      </section>

      <aside class="objective-surface__mentor">
        <Card class="objective-card objective-card--analysis">
          <CardHeader>
            <p class="eyebrow">AI mentor</p>
            <CardTitle>{{ objectiveInfo.review_title }}</CardTitle>
          </CardHeader>
          <CardContent>
            <p class="objective-copy">{{ objectiveInfo.review_copy }}</p>
            <div class="objective-mentor-grid">
              <div>
                <span class="objective-mini-stats__label">Focus</span>
                <strong>{{ objectiveInfo.lens_title }}</strong>
              </div>
              <div>
                <span class="objective-mini-stats__label">Template</span>
                <strong>{{ objectiveInfo.badge }}</strong>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card class="objective-card">
          <CardHeader>
            <p class="eyebrow">Seleção atual</p>
            <CardTitle>{{ selectedOptions.length ? 'Resposta em construção' : 'Nenhuma opção marcada' }}</CardTitle>
          </CardHeader>
          <CardContent>
            <div v-if="selectedLabels.length" class="objective-selection-stack">
              <Badge v-for="label in selectedLabels" :key="label" variant="outline">{{ label }}</Badge>
            </div>
            <p v-else class="objective-copy objective-copy--muted">
              Marque uma ou mais alternativas para ver a síntese da resposta aqui.
            </p>
            <div v-if="selectedMisconceptions.length" class="objective-misconceptions">
              <span class="objective-mini-stats__label">Misconceptions capturadas</span>
              <Badge v-for="item in selectedMisconceptions" :key="item" variant="outline">{{ item }}</Badge>
            </div>
          </CardContent>
        </Card>

        <Card class="objective-card objective-card--note">
          <CardHeader>
            <p class="eyebrow">Leitura final</p>
            <CardTitle>{{ objectiveInfo.action_title }}</CardTitle>
          </CardHeader>
          <CardContent>
            <p class="objective-copy">{{ objectiveInfo.lens_copy }}</p>
            <div class="objective-note-footer">
              <Timer :size="16" />
              <span>{{ estimatedTime }} min · {{ contextTags.join(' · ') || 'contexto objetivo' }}</span>
            </div>
          </CardContent>
        </Card>
      </aside>
    </div>
  </div>
</template>

<style scoped>
.objective-surface {
  display: grid;
  gap: 1rem;
  min-height: 0;
}

.objective-surface__hero {
  overflow: hidden;
}

.objective-surface__hero-header {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 1rem;
  align-items: stretch;
}

.objective-surface__hero-copy {
  display: grid;
  gap: 0.8rem;
}

.objective-surface__hero-title {
  font-size: clamp(2rem, 3vw, 3.6rem);
  line-height: 0.92;
  letter-spacing: -0.08em;
  text-transform: uppercase;
}

.objective-surface__hero-description {
  max-width: 54rem;
  line-height: 1.55;
}

.objective-surface__hero-pills {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.objective-surface__hero-metrics {
  display: grid;
  grid-template-columns: repeat(2, minmax(8.8rem, 1fr));
  gap: 0.75rem;
  align-self: start;
}

.objective-metric {
  display: grid;
  gap: 0.3rem;
  padding: 0.85rem 0.95rem;
  border: 2px solid var(--on-surface);
  background: color-mix(in srgb, var(--surface-container) 82%, var(--primary) 18%);
  box-shadow: 4px 4px 0 0 var(--on-surface);
}

.objective-metric__label {
  font-size: 0.68rem;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.16em;
  color: var(--on-surface-variant);
}

.objective-metric strong {
  font-size: 0.98rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.objective-surface__layout {
  display: grid;
  grid-template-columns: minmax(17rem, 22rem) minmax(0, 1fr) minmax(18rem, 21rem);
  gap: 1rem;
  min-height: 0;
  align-items: start;
}

.objective-surface__aside,
.objective-surface__main,
.objective-surface__mentor {
  display: grid;
  gap: 1rem;
  min-height: 0;
}

.objective-card {
  overflow: hidden;
  border: 2px solid var(--on-surface);
  box-shadow: 4px 4px 0 0 var(--on-surface);
  background: color-mix(in srgb, var(--surface) 94%, var(--primary) 6%);
}

.objective-card--featured {
  background: color-mix(in srgb, var(--surface) 88%, var(--primary-container) 12%);
}

.objective-card--dark {
  background: var(--on-surface);
  color: var(--surface);
  box-shadow: 4px 4px 0 0 color-mix(in srgb, var(--primary) 72%, var(--on-surface));
}

.objective-card--analysis {
  background: color-mix(in srgb, var(--surface) 88%, #d9f0dd 12%);
  box-shadow: 4px 4px 0 0 color-mix(in srgb, #2f9e44 75%, var(--on-surface));
  border-color: #2f9e44;
}

.objective-card--note {
  background: color-mix(in srgb, var(--on-surface) 94%, var(--primary) 6%);
  color: var(--surface);
}

.objective-card--choices {
  background: color-mix(in srgb, var(--surface) 96%, var(--primary) 4%);
}

.objective-card--progress {
  background: color-mix(in srgb, var(--surface) 92%, var(--primary) 8%);
}

.objective-copy {
  margin: 0;
  line-height: 1.55;
}

.objective-copy--inverse {
  color: color-mix(in srgb, var(--surface) 92%, white 8%);
}

.objective-copy--muted {
  color: var(--muted-foreground);
}

.objective-note-footer {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  margin-top: 0.95rem;
  font-size: 0.82rem;
  font-weight: 600;
}

.objective-badge-cloud,
.objective-selection-stack,
.objective-misconceptions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.objective-mini-stats {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.75rem;
  margin-top: 0.95rem;
}

.objective-mini-stats > div,
.objective-mentor-grid > div {
  display: grid;
  gap: 0.25rem;
}

.objective-mini-stats__label {
  font-size: 0.65rem;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: color-mix(in srgb, currentColor 68%, transparent);
}

.objective-frame {
  display: grid;
  gap: 0;
  overflow: hidden;
}

.objective-frame__chrome {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0.75rem 0.95rem;
  border-bottom: 2px solid var(--on-surface);
  background: color-mix(in srgb, var(--surface-container) 94%, var(--surface));
}

.objective-frame__lights {
  display: flex;
  gap: 0.35rem;
}

.objective-frame__light {
  width: 0.72rem;
  height: 0.72rem;
  border: 2px solid var(--on-surface);
  background: color-mix(in srgb, var(--surface-container-high) 70%, var(--primary) 30%);
}

.objective-frame__title {
  font-size: 0.72rem;
  font-weight: 800;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: var(--on-surface-variant);
  text-align: center;
  flex: 1;
}

.objective-frame__content {
  padding: 0;
}

.objective-frame__footer {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 0.75rem;
  align-items: center;
  padding: 0.8rem 0.95rem;
  border-top: 2px solid var(--on-surface);
  background: color-mix(in srgb, var(--surface-container) 92%, var(--primary) 8%);
}

.objective-frame__footer-copy {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  font-size: 0.8rem;
  font-weight: 600;
}

.objective-frame__footer-copy--muted {
  color: var(--on-surface-variant);
}

.objective-surface__choices-list {
  display: grid;
  gap: 0.85rem;
}

.objective-choice {
  display: grid;
  grid-template-columns: auto auto minmax(0, 1fr);
  gap: 0.9rem;
  width: 100%;
  text-align: left;
  align-items: start;
  padding: 1rem 1.05rem;
  border: 2px solid var(--on-surface);
  background: color-mix(in srgb, var(--surface) 92%, var(--primary) 8%);
  box-shadow: 4px 4px 0 0 var(--on-surface);
  transition:
    transform 140ms ease,
    box-shadow 140ms ease,
    background 140ms ease,
    border-color 140ms ease;
}

.objective-choice:hover:not(:disabled) {
  transform: translate(2px, 2px);
  box-shadow: 2px 2px 0 0 var(--on-surface);
}

.objective-choice--selected {
  border-color: var(--primary);
  background: color-mix(in srgb, var(--surface) 86%, var(--primary-container) 14%);
  box-shadow: 4px 4px 0 0 var(--primary);
}

.objective-choice__marker {
  display: flex;
  align-items: flex-start;
  padding-top: 0.1rem;
}

.objective-choice__body {
  display: grid;
  gap: 0.45rem;
}

.objective-choice__label-row {
  display: flex;
  justify-content: space-between;
  gap: 0.75rem;
  align-items: center;
}

.objective-choice__body p {
  margin: 0;
  font-size: 0.98rem;
  line-height: 1.5;
  font-weight: 700;
}

.objective-choice__body small {
  color: var(--on-surface-variant);
  line-height: 1.45;
}

.objective-progress {
  display: grid;
  gap: 0.7rem;
}

.objective-progress__row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  padding-top: 0.4rem;
  border-top: 1px solid color-mix(in srgb, var(--on-surface) 12%, transparent);
  font-size: 0.9rem;
}

.objective-progress__row:first-child {
  border-top: 0;
  padding-top: 0;
}

.objective-mentor-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.75rem;
  margin-top: 0.9rem;
}

.objective-card :deep(.card-header) {
  gap: 0.45rem;
}

@media (max-width: 1360px) {
  .objective-surface__layout {
    grid-template-columns: minmax(17rem, 20rem) minmax(0, 1fr);
  }

  .objective-surface__mentor {
    grid-column: 1 / -1;
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 1120px) {
  .objective-surface__hero-header,
  .objective-surface__layout,
  .objective-surface__mentor {
    grid-template-columns: 1fr;
  }

  .objective-surface__hero-metrics {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .objective-surface__aside,
  .objective-surface__main,
  .objective-surface__mentor {
    grid-column: auto;
  }
}

@media (max-width: 760px) {
  .objective-surface__hero-metrics,
  .objective-mentor-grid,
  .objective-mini-stats {
    grid-template-columns: 1fr;
  }

  .objective-choice {
    grid-template-columns: auto minmax(0, 1fr);
  }
}
</style>
