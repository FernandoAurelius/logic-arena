<script setup lang="ts">
import { computed } from 'vue'
import { GitCompareArrows, LockKeyhole, WandSparkles } from 'lucide-vue-next'

import type { SessionConfig } from '@/entities/practice-session'
import { Badge } from '@/shared/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/shared/ui/card'
import MonacoEditor from '@/shared/ui/editor/MonacoEditor.vue'

import {
  getRestrictedEditableCode,
  getRestrictedInstructions,
  getRestrictedLanguage,
  getRestrictedOriginalCode,
  getRestrictedTemplateMeta,
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

const language = computed(() => getRestrictedLanguage(props.sessionConfig))
const originalCode = computed(() => getRestrictedOriginalCode(props.sessionConfig))
const editableCode = computed(() => getRestrictedEditableCode(props.sessionConfig))
const instructions = computed(() => getRestrictedInstructions(props.sessionConfig))
const templateMeta = computed(() => getRestrictedTemplateMeta(props.sessionConfig))
const analysisSteps = computed(() => (templateMeta.value.analysis_steps ?? []) as string[])

if (!code.value) {
  code.value = editableCode.value
}
</script>

<template>
  <div class="restricted-diff">
    <Card class="restricted-diff__hero">
      <CardHeader class="restricted-diff__hero-header">
        <div>
          <p class="eyebrow">Fase 4 · restricted_code</p>
          <CardTitle>{{ props.exerciseTitle }}</CardTitle>
          <CardDescription>
            Corrija o snippet com o menor diff possível e valide a estrutura antes de submeter.
          </CardDescription>
        </div>
        <div class="restricted-diff__hero-badges">
          <Badge>restricted_diff</Badge>
          <Badge variant="outline">{{ language }}</Badge>
          <Badge variant="outline">{{ props.readOnly ? 'somente leitura' : 'edição guiada' }}</Badge>
        </div>
      </CardHeader>
      <CardContent class="restricted-diff__hero-content">
        <div class="restricted-diff__guide">
          <div class="restricted-diff__guide-block">
            <p class="section-label">Objetivo</p>
            <strong>Corrigir sem reescrever</strong>
            <p>{{ instructions || 'Mantenha o contexto do snippet e altere apenas o que for necessário.' }}</p>
          </div>
          <div class="restricted-diff__guide-block">
            <p class="section-label">Checklist</p>
            <ul>
              <li v-for="step in analysisSteps" :key="step">{{ step }}</li>
            </ul>
          </div>
        </div>
      </CardContent>
    </Card>

    <div class="restricted-diff__grid">
      <Card class="restricted-diff__panel">
        <CardHeader class="restricted-diff__panel-header">
          <div class="restricted-diff__panel-title">
            <LockKeyhole :size="16" />
            <CardTitle>Original bloqueado</CardTitle>
          </div>
          <CardDescription>Referência para comparar a correção.</CardDescription>
        </CardHeader>
        <CardContent class="restricted-diff__editor-content">
          <MonacoEditor
            :model-value="originalCode"
            :language="language"
            height="calc(100vh - 23rem)"
            read-only
          />
        </CardContent>
      </Card>

      <Card class="restricted-diff__panel">
        <CardHeader class="restricted-diff__panel-header">
          <div class="restricted-diff__panel-title">
            <GitCompareArrows :size="16" />
            <CardTitle>Snippet corrigido</CardTitle>
          </div>
          <CardDescription>Edite o lado direito até satisfazer os critérios estruturais.</CardDescription>
        </CardHeader>
        <CardContent class="restricted-diff__editor-content">
          <MonacoEditor
            v-model="code"
            :language="language"
            height="calc(100vh - 23rem)"
            :read-only="props.readOnly"
            placeholder="# aplique a menor correção possível"
          />
        </CardContent>
      </Card>
    </div>

    <Card class="restricted-diff__footer">
      <CardContent class="restricted-diff__footer-content">
        <WandSparkles :size="16" />
        <p>
          A avaliação desta família olha para critérios estruturais e mudanças localizadas. Quanto menor e mais precisa
          a correção, melhor tende a ser a leitura pedagógica da tentativa.
        </p>
      </CardContent>
    </Card>
  </div>
</template>

<style scoped>
.restricted-diff {
  display: grid;
  gap: 1rem;
  min-height: 0;
}

.restricted-diff__hero-header,
.restricted-diff__panel-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
}

.restricted-diff__hero-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  justify-content: flex-end;
}

.restricted-diff__guide {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1rem;
}

.restricted-diff__guide-block {
  border: 1px solid color-mix(in srgb, var(--border) 85%, transparent);
  border-radius: 1rem;
  padding: 1rem;
  background: color-mix(in srgb, var(--surface) 92%, var(--accent) 8%);
}

.restricted-diff__guide-block ul {
  margin: 0.5rem 0 0;
  padding-left: 1.1rem;
  display: grid;
  gap: 0.45rem;
}

.restricted-diff__grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1rem;
  min-height: 0;
}

.restricted-diff__panel {
  display: grid;
  grid-template-rows: auto 1fr;
  min-height: 0;
}

.restricted-diff__panel-title {
  display: flex;
  align-items: center;
  gap: 0.55rem;
}

.restricted-diff__editor-content {
  min-height: 0;
  overflow: hidden;
  padding-top: 0;
}

.restricted-diff__footer-content {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
}

@media (max-width: 1120px) {
  .restricted-diff__guide,
  .restricted-diff__grid {
    grid-template-columns: 1fr;
  }
}
</style>
