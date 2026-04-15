<script setup lang="ts">
import { computed } from 'vue'
import { Activity, Binary, Circle, AlertTriangle } from 'lucide-vue-next'

import type { SessionConfig } from '@/entities/practice-session'
import { Badge } from '@/shared/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/shared/ui/card'
import MonacoEditor from '@/shared/ui/editor/MonacoEditor.vue'

import {
  getObjectiveOptions,
  getObjectiveSnippet,
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
const templateLabel = computed(() => {
  if (snippet.value.template === 'compile-runtime-output') return 'Compile / Runtime / Output'
  if (snippet.value.template === 'behavior-classification') return 'Behavior classification'
  return 'Objective classifier'
})

function iconForOption(key: string) {
  const normalized = key.toLowerCase()
  if (normalized.includes('compile')) return AlertTriangle
  if (normalized.includes('runtime')) return Activity
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
        <div>
          <p class="eyebrow">Diagnóstico exam-like</p>
          <CardTitle>{{ props.exerciseTitle }}</CardTitle>
          <CardDescription>
            Classifique com precisão o comportamento do snippet antes de submeter.
          </CardDescription>
        </div>
        <div class="classifier-surface__hero-badges">
          <Badge>{{ templateLabel }}</Badge>
          <Badge variant="outline">{{ props.sessionConfig?.surface_key ?? 'objective_classifier' }}</Badge>
        </div>
      </CardHeader>
    </Card>

    <div class="classifier-surface__grid">
      <Card class="classifier-surface__snippet">
        <CardHeader>
          <p class="eyebrow">Snippet</p>
          <CardTitle>Leitura técnica</CardTitle>
          <CardDescription>
            Avalie compilação, execução e comportamento observável antes de marcar a resposta.
          </CardDescription>
        </CardHeader>
        <CardContent class="classifier-surface__snippet-content">
          <MonacoEditor
            :model-value="snippet.code"
            :language="snippet.language"
            height="24rem"
            :read-only="true"
          />
        </CardContent>
      </Card>

      <Card class="classifier-surface__panel">
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
            @click="selectOption(option.canonical_key ?? option.key)"
          >
            <component :is="iconForOption(option.canonical_key ?? option.key)" :size="18" />
            <div class="classifier-option__body">
              <strong>{{ option.label }}</strong>
              <small v-if="option.explanation">{{ option.explanation }}</small>
            </div>
          </button>
        </CardContent>
      </Card>
    </div>
  </div>
</template>

<style scoped>
.classifier-surface {
  display: grid;
  gap: 1rem;
  min-height: 0;
}

.classifier-surface__hero-header,
.classifier-surface__hero-badges {
  display: flex;
  gap: 0.75rem;
  justify-content: space-between;
  flex-wrap: wrap;
}

.classifier-surface__grid {
  display: grid;
  grid-template-columns: minmax(0, 1.15fr) minmax(20rem, 0.85fr);
  gap: 1rem;
  min-height: 0;
}

.classifier-surface__snippet-content {
  padding-top: 0;
}

.classifier-surface__panel {
  min-height: 0;
}

.classifier-surface__options {
  display: grid;
  gap: 0.8rem;
}

.classifier-option {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 0.8rem;
  align-items: start;
  padding: 1rem;
  text-align: left;
  border: 2px solid var(--foreground);
  background: color-mix(in srgb, var(--background) 93%, var(--accent) 7%);
  box-shadow: 4px 4px 0 0 color-mix(in srgb, var(--foreground) 88%, transparent);
  transition:
    transform 140ms ease,
    box-shadow 140ms ease,
    background 140ms ease;
}

.classifier-option:hover:not(:disabled) {
  transform: translate(2px, 2px);
  box-shadow: 2px 2px 0 0 color-mix(in srgb, var(--foreground) 88%, transparent);
}

.classifier-option--selected {
  background: color-mix(in srgb, var(--primary-container) 34%, var(--background));
}

.classifier-option__body {
  display: grid;
  gap: 0.35rem;
}

.classifier-option__body small {
  line-height: 1.45;
  color: var(--muted-foreground);
}

@media (max-width: 1120px) {
  .classifier-surface__grid {
    grid-template-columns: 1fr;
  }
}
</style>
