<script setup lang="ts">
import { computed } from 'vue'
import { CheckCircle2, Circle, Clock3 } from 'lucide-vue-next'

import type { SessionConfig } from '@/entities/practice-session'
import { Badge } from '@/shared/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/shared/ui/card'
import MonacoEditor from '@/shared/ui/editor/MonacoEditor.vue'

import {
  formatAttemptMode,
  formatObjectiveOptionMarker,
  getObjectiveLearningObjectives,
  getObjectiveOptions,
  getObjectiveSnippet,
  getObjectiveStatement,
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

const exercise = computed(() => props.sessionConfig?.exercise ?? null)
const options = computed(() => getObjectiveOptions(props.sessionConfig))
const snippet = computed(() => getObjectiveSnippet(props.sessionConfig))
const allowMultiple = computed(() => isObjectiveMultiple(props.sessionConfig))
const objectiveStatement = computed(() => getObjectiveStatement(props.sessionConfig))
const learningObjectives = computed(() => getObjectiveLearningObjectives(props.sessionConfig))
const modeLabel = computed(() => formatAttemptMode(props.sessionConfig?.mode))
const difficulty = computed(() => exercise.value?.difficulty ?? 'intermediário')
const estimatedTime = computed(() => exercise.value?.estimated_time_minutes ?? 10)
const trackName = computed(() => exercise.value?.track_name ?? '')
const moduleName = computed(() => exercise.value?.module_name ?? '')
const trackStep = computed(() => exercise.value?.track_position ?? 0)
const contextSummary = computed(() =>
  [
    exercise.value?.concept_summary,
    exercise.value?.pedagogical_brief,
    exercise.value?.professor_note,
  ]
    .map((item) => String(item ?? '').trim())
    .find(Boolean) ?? '',
)

function toggleOption(key: string) {
  if (props.readOnly) return
  selectedOptions.value = toggleObjectiveSelection(selectedOptions.value, key, allowMultiple.value)
}

function isSelected(key: string) {
  return selectedOptions.value.includes(key)
}
</script>

<template>
  <div class="objective-clean">
    <header class="objective-clean__header">
      <div class="objective-clean__eyebrow">
        <span v-if="trackName">{{ trackName }}</span>
        <span v-if="trackStep > 0">Etapa {{ trackStep }}</span>
        <span v-else>{{ modeLabel }}</span>
      </div>
      <div class="objective-clean__meta">
        <Badge variant="outline">{{ difficulty }}</Badge>
        <Badge variant="outline">
          <Clock3 :size="14" />
          {{ estimatedTime }} min
        </Badge>
        <Badge v-if="allowMultiple" variant="outline">múltiplas respostas</Badge>
      </div>
    </header>

    <Card class="objective-clean__statement-card">
      <CardHeader class="objective-clean__statement-header">
        <div>
          <p class="eyebrow">Enunciado</p>
          <CardTitle class="objective-clean__title">{{ props.exerciseTitle }}</CardTitle>
          <CardDescription v-if="moduleName">{{ moduleName }}</CardDescription>
        </div>
      </CardHeader>
      <CardContent class="objective-clean__statement-body">
        <p class="objective-clean__statement">{{ objectiveStatement }}</p>
        <p v-if="contextSummary" class="objective-clean__support">{{ contextSummary }}</p>
        <div v-if="learningObjectives.length" class="objective-clean__goals">
          <Badge v-for="item in learningObjectives.slice(0, 3)" :key="item" variant="outline">
            {{ item }}
          </Badge>
        </div>
      </CardContent>
    </Card>

    <Card v-if="snippet.lineCount > 0" class="objective-clean__snippet-card">
      <CardHeader>
        <p class="eyebrow">Trecho de referência</p>
        <CardTitle>{{ snippet.title }}</CardTitle>
        <CardDescription>Use o estímulo apenas como leitura; a decisão vem da interpretação.</CardDescription>
      </CardHeader>
      <CardContent class="objective-clean__snippet-body">
        <MonacoEditor
          :model-value="snippet.code"
          :language="snippet.language"
          height="18rem"
          :read-only="true"
        />
      </CardContent>
    </Card>

    <Card class="objective-clean__choices-card">
      <CardHeader>
        <p class="eyebrow">Alternativas</p>
        <CardTitle>
          {{ allowMultiple ? 'Selecione todas as corretas' : 'Escolha a melhor resposta' }}
        </CardTitle>
      </CardHeader>
      <CardContent class="objective-clean__choices">
        <button
          v-for="(option, index) in options"
          :key="option.canonical_key ?? option.key"
          class="objective-clean__choice"
          :class="{ 'objective-clean__choice--selected': isSelected(option.canonical_key ?? option.key) }"
          type="button"
          :disabled="props.readOnly"
          :aria-pressed="isSelected(option.canonical_key ?? option.key)"
          @click="toggleOption(option.canonical_key ?? option.key)"
        >
          <div class="objective-clean__choice-leading">
            <span class="objective-clean__choice-marker">
              {{ formatObjectiveOptionMarker(option, index) }}
            </span>
            <span class="objective-clean__choice-icon" aria-hidden="true">
              <CheckCircle2 v-if="isSelected(option.canonical_key ?? option.key)" :size="18" />
              <Circle v-else :size="18" />
            </span>
          </div>
          <p class="objective-clean__choice-text">{{ option.text }}</p>
        </button>
      </CardContent>
    </Card>
  </div>
</template>

<style scoped>
.objective-clean {
  display: grid;
  gap: 1rem;
  min-height: 0;
}

.objective-clean__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
}

.objective-clean__eyebrow {
  display: flex;
  flex-wrap: wrap;
  gap: 0.55rem;
  font-family: 'Space Grotesk', sans-serif;
  font-size: 0.8rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--primary);
}

.objective-clean__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.objective-clean__title {
  font-size: clamp(1.9rem, 3vw, 2.8rem);
  line-height: 0.95;
  letter-spacing: -0.04em;
  text-transform: uppercase;
}

.objective-clean__statement-card,
.objective-clean__snippet-card,
.objective-clean__choices-card {
  box-shadow: 6px 6px 0 color-mix(in srgb, var(--primary) 22%, transparent);
}

.objective-clean__statement-header {
  padding-bottom: 0.5rem;
}

.objective-clean__statement-body {
  display: grid;
  gap: 1rem;
}

.objective-clean__statement {
  font-size: 1.24rem;
  line-height: 1.65;
  color: var(--on-surface);
}

.objective-clean__support {
  font-size: 1rem;
  line-height: 1.7;
  color: var(--muted-foreground);
}

.objective-clean__goals {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.objective-clean__snippet-body {
  padding-top: 0;
}

.objective-clean__choices {
  display: grid;
  gap: 0.85rem;
}

.objective-clean__choice {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 1rem;
  align-items: flex-start;
  width: 100%;
  padding: 1rem 1.1rem;
  border: 2px solid var(--outline);
  background: color-mix(in srgb, var(--surface) 92%, white);
  text-align: left;
  transition: transform 140ms ease, box-shadow 140ms ease, border-color 140ms ease;
}

.objective-clean__choice:hover:not(:disabled) {
  transform: translate(-2px, -2px);
  box-shadow: 6px 6px 0 color-mix(in srgb, var(--primary) 20%, transparent);
  border-color: var(--primary);
}

.objective-clean__choice--selected {
  border-color: var(--primary);
  background: color-mix(in srgb, var(--primary-container) 22%, var(--surface));
  box-shadow: 6px 6px 0 color-mix(in srgb, var(--primary) 22%, transparent);
}

.objective-clean__choice-leading {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.objective-clean__choice-marker {
  min-width: 2rem;
  font-family: 'Space Grotesk', sans-serif;
  font-size: 1rem;
  font-weight: 700;
  color: var(--primary);
}

.objective-clean__choice-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: var(--primary);
}

.objective-clean__choice-text {
  font-size: 1.02rem;
  line-height: 1.65;
  color: var(--on-surface);
}

@media (max-width: 900px) {
  .objective-clean__title {
    font-size: 1.7rem;
  }

  .objective-clean__statement {
    font-size: 1.08rem;
  }

  .objective-clean__choice {
    grid-template-columns: 1fr;
    gap: 0.75rem;
  }
}
</style>
