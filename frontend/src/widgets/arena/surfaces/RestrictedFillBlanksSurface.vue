<script setup lang="ts">
import { computed, reactive, watch } from 'vue'
import { BetweenHorizontalStart, ScanSearch, SquarePen } from 'lucide-vue-next'

import type { SessionConfig } from '@/entities/practice-session'
import { Badge } from '@/shared/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/shared/ui/card'
import MonacoEditor from '@/shared/ui/editor/MonacoEditor.vue'
import { Input } from '@/shared/ui/input'

import {
  extractBlankAnswers,
  getRestrictedBlankTemplate,
  getRestrictedBlanks,
  getRestrictedInstructions,
  getRestrictedLanguage,
  getRestrictedTemplateMeta,
  renderBlankTemplate,
} from './restrictedSurfaceShared'

const code = defineModel<string>('code', { default: '' })

const props = withDefaults(defineProps<{
  readOnly?: boolean
  exerciseTitle?: string
  sessionConfig?: SessionConfig | null
}>(), {
  readOnly: false,
  exerciseTitle: 'atividade',
  sessionConfig: null,
})

const blankTemplate = computed(() => getRestrictedBlankTemplate(props.sessionConfig))
const blanks = computed(() => getRestrictedBlanks(props.sessionConfig))
const instructions = computed(() => getRestrictedInstructions(props.sessionConfig))
const language = computed(() => getRestrictedLanguage(props.sessionConfig))
const templateMeta = computed(() => getRestrictedTemplateMeta(props.sessionConfig))
const analysisSteps = computed(() => (templateMeta.value.analysis_steps ?? []) as string[])
const blankAnswers = reactive<Record<string, string>>({})

function syncAnswersFromCode(sourceCode: string) {
  const extracted = extractBlankAnswers(blankTemplate.value, sourceCode)
  for (const blank of blanks.value) {
    blankAnswers[blank.key] = extracted[blank.key] ?? blankAnswers[blank.key] ?? ''
  }
}

watch(
  () => code.value,
  (value) => {
    syncAnswersFromCode(value)
  },
  { immediate: true },
)

watch(
  [blankTemplate, blanks],
  () => {
    if (!code.value) {
      code.value = renderBlankTemplate(blankTemplate.value, blankAnswers)
    }
    syncAnswersFromCode(code.value)
  },
  { immediate: true },
)

watch(
  blankAnswers,
  () => {
    const rendered = renderBlankTemplate(blankTemplate.value, blankAnswers)
    if (rendered !== code.value) {
      code.value = rendered
    }
  },
  { deep: true },
)
</script>

<template>
  <div class="restricted-fill">
    <Card class="restricted-fill__hero">
      <CardHeader class="restricted-fill__hero-header">
        <div>
          <p class="eyebrow">Fase 4 · restricted_code</p>
          <CardTitle>{{ props.exerciseTitle }}</CardTitle>
          <CardDescription>
            Preencha as lacunas de forma controlada e valide o trecho completo antes de submeter.
          </CardDescription>
        </div>
        <div class="restricted-fill__hero-badges">
          <Badge>restricted_fill_blanks</Badge>
          <Badge variant="outline">{{ blanks.length }} lacuna(s)</Badge>
          <Badge variant="outline">{{ language }}</Badge>
        </div>
      </CardHeader>
      <CardContent class="restricted-fill__hero-content">
        <p>{{ instructions || 'Cada lacuna representa uma decisão estrutural específica da solução.' }}</p>
      </CardContent>
    </Card>

    <div class="restricted-fill__grid">
      <Card class="restricted-fill__form">
        <CardHeader>
          <div class="restricted-fill__title">
            <SquarePen :size="16" />
            <CardTitle>Preencha as lacunas</CardTitle>
          </div>
          <CardDescription>As entradas abaixo atualizam o código final em tempo real.</CardDescription>
        </CardHeader>
        <CardContent class="restricted-fill__inputs">
          <div v-for="blank in blanks" :key="blank.key" class="restricted-fill__input-row">
            <label :for="blank.key">
              <span>{{ blank.label }}</span>
              <small v-if="blank.hint">{{ blank.hint }}</small>
            </label>
            <Input
              :id="blank.key"
              v-model="blankAnswers[blank.key]"
              :placeholder="blank.placeholder || 'preencha aqui'"
              :disabled="props.readOnly"
            />
          </div>
          <div class="restricted-fill__analysis">
            <p class="section-label">Checklist</p>
            <ul>
              <li v-for="step in analysisSteps" :key="step">{{ step }}</li>
            </ul>
          </div>
        </CardContent>
      </Card>

      <Card class="restricted-fill__preview">
        <CardHeader>
          <div class="restricted-fill__title">
            <BetweenHorizontalStart :size="16" />
            <CardTitle>Prévia estruturada</CardTitle>
          </div>
          <CardDescription>Este é o código final que será enviado para validação estrutural.</CardDescription>
        </CardHeader>
        <CardContent class="restricted-fill__preview-content">
          <MonacoEditor
            v-model="code"
            :language="language"
            height="calc(100vh - 23rem)"
            :read-only="props.readOnly"
          />
        </CardContent>
      </Card>
    </div>

    <Card class="restricted-fill__footer">
      <CardContent class="restricted-fill__footer-content">
        <ScanSearch :size="16" />
        <p>
          O validador desta família avalia o código completo renderizado a partir das lacunas. Revise o snippet final
          antes de enviar para evitar erro de encaixe entre blanks.
        </p>
      </CardContent>
    </Card>
  </div>
</template>

<style scoped>
.restricted-fill {
  display: grid;
  gap: 1rem;
  min-height: 0;
}

.restricted-fill__hero-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}

.restricted-fill__hero-badges,
.restricted-fill__title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.restricted-fill__hero-badges {
  flex-wrap: wrap;
  justify-content: flex-end;
}

.restricted-fill__grid {
  display: grid;
  grid-template-columns: 22rem minmax(0, 1fr);
  gap: 1rem;
  min-height: 0;
}

.restricted-fill__form,
.restricted-fill__preview {
  display: grid;
  grid-template-rows: auto 1fr;
  min-height: 0;
}

.restricted-fill__inputs {
  display: grid;
  gap: 1rem;
  align-content: start;
}

.restricted-fill__input-row {
  display: grid;
  gap: 0.45rem;
}

.restricted-fill__input-row label {
  display: grid;
  gap: 0.2rem;
}

.restricted-fill__input-row small {
  color: var(--muted-foreground);
}

.restricted-fill__analysis {
  border-top: 1px solid var(--border);
  padding-top: 1rem;
}

.restricted-fill__analysis ul {
  margin: 0.5rem 0 0;
  padding-left: 1.1rem;
  display: grid;
  gap: 0.45rem;
}

.restricted-fill__preview-content {
  min-height: 0;
  overflow: hidden;
  padding-top: 0;
}

.restricted-fill__footer-content {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
}

@media (max-width: 1120px) {
  .restricted-fill__grid {
    grid-template-columns: 1fr;
  }
}
</style>
