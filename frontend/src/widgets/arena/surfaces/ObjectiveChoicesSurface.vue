<script setup lang="ts">
import { computed } from 'vue'
import { CheckCircle2, Circle, Code2, ListChecks } from 'lucide-vue-next'

import type { SessionConfig } from '@/entities/practice-session'
import { Badge } from '@/shared/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/shared/ui/card'
import MonacoEditor from '@/shared/ui/editor/MonacoEditor.vue'

import {
  getObjectiveOptions,
  getObjectiveSnippet,
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

function toggleOption(key: string) {
  if (props.readOnly) return
  selectedOptions.value = toggleObjectiveSelection(selectedOptions.value, key, allowMultiple.value)
}
</script>

<template>
  <div class="objective-surface">
    <Card class="objective-surface__hero">
      <CardHeader class="objective-surface__hero-header">
        <div>
          <p class="eyebrow">Item objetivo com estímulo</p>
          <CardTitle>{{ props.exerciseTitle }}</CardTitle>
          <CardDescription>
            Escolha
            {{ allowMultiple ? 'todas as alternativas corretas' : 'a alternativa correta' }}
            com base no estímulo e nas regras do item.
          </CardDescription>
        </div>
        <div class="objective-surface__hero-badges">
          <Badge>{{ props.sessionConfig?.surface_key ?? 'objective_choices' }}</Badge>
          <Badge variant="outline">{{ allowMultiple ? 'múltipla resposta' : 'resposta única' }}</Badge>
          <Badge variant="outline">{{ options.length }} alternativas</Badge>
        </div>
      </CardHeader>
      <CardContent class="objective-surface__hero-content">
        <div class="objective-surface__summary">
          <div class="objective-stat">
            <ListChecks :size="16" />
            <span>{{ selectedOptions.length }} selecionada(s)</span>
          </div>
          <div class="objective-stat">
            <Code2 :size="16" />
            <span>{{ snippet.code ? 'com snippet read-only' : 'sem snippet adicional' }}</span>
          </div>
        </div>
      </CardContent>
    </Card>

    <div class="objective-surface__grid">
      <Card v-if="snippet.code" class="objective-surface__stimulus">
        <CardHeader>
          <p class="eyebrow">Estímulo</p>
          <CardTitle>Snippet de referência</CardTitle>
          <CardDescription>
            Leia o código com cuidado antes de decidir. Esta área é somente leitura.
          </CardDescription>
        </CardHeader>
        <CardContent class="objective-surface__stimulus-content">
          <MonacoEditor
            :model-value="snippet.code"
            :language="snippet.language"
            height="22rem"
            :read-only="true"
          />
        </CardContent>
      </Card>

      <Card class="objective-surface__choices">
        <CardHeader>
          <p class="eyebrow">Alternativas</p>
          <CardTitle>Escolha fundamentada</CardTitle>
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
              <small v-if="option.explanation">{{ option.explanation }}</small>
            </div>
          </button>
        </CardContent>
      </Card>
    </div>
  </div>
</template>

<style scoped>
.objective-surface {
  display: grid;
  gap: 1rem;
  min-height: 0;
}

.objective-surface__hero-header,
.objective-surface__hero-badges {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
  justify-content: space-between;
}

.objective-surface__hero-content {
  padding-top: 0;
}

.objective-surface__summary {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.objective-stat {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  padding: 0.6rem 0.8rem;
  border: 2px solid var(--foreground);
  box-shadow: 4px 4px 0 0 color-mix(in srgb, var(--foreground) 88%, transparent);
  background: color-mix(in srgb, var(--background) 88%, var(--primary-container) 12%);
  font-weight: 600;
}

.objective-surface__grid {
  display: grid;
  grid-template-columns: minmax(0, 1.05fr) minmax(0, 1fr);
  gap: 1rem;
  min-height: 0;
}

.objective-surface__stimulus,
.objective-surface__choices {
  min-height: 0;
}

.objective-surface__stimulus-content {
  padding-top: 0;
}

.objective-surface__choices-list {
  display: grid;
  gap: 0.85rem;
}

.objective-choice {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 0.9rem;
  width: 100%;
  text-align: left;
  padding: 1rem;
  border: 2px solid var(--foreground);
  background: color-mix(in srgb, var(--background) 92%, var(--primary-container) 8%);
  box-shadow: 4px 4px 0 0 color-mix(in srgb, var(--foreground) 88%, transparent);
  transition:
    transform 140ms ease,
    box-shadow 140ms ease,
    background 140ms ease;
}

.objective-choice:hover:not(:disabled) {
  transform: translate(2px, 2px);
  box-shadow: 2px 2px 0 0 color-mix(in srgb, var(--foreground) 88%, transparent);
}

.objective-choice--selected {
  background: color-mix(in srgb, var(--primary-container) 36%, var(--background));
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
}

.objective-choice__body small {
  color: var(--muted-foreground);
  line-height: 1.45;
}

@media (max-width: 1120px) {
  .objective-surface__grid {
    grid-template-columns: 1fr;
  }
}
</style>
