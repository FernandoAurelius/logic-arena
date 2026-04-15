<script setup lang="ts">
import type { SessionConfig } from '@/entities/practice-session'
import { Badge } from '@/shared/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card'
import { Separator } from '@/shared/ui/separator'

import type { ArenaSurfaceDescriptor } from './arenaSurfaceRegistry'

const props = defineProps<{
  surface: ArenaSurfaceDescriptor
  exerciseTitle?: string
  sessionConfig?: SessionConfig | null
}>()

function surfaceSubtitle() {
  if (props.surface.kind === 'objective') {
    return 'Leitura de estímulo, classificação objetiva e feedback ancorado em gabarito.'
  }
  if (props.surface.kind === 'restricted') {
    return 'Correção localizada com regiões editáveis e validação estrutural.'
  }
  if (props.surface.kind === 'contract') {
    return 'Evidência de contrato observável entre intenção, implementação e comportamento.'
  }
  return 'Resposta escrita guiada por rubrica e revisão assistida.'
}
</script>

<template>
  <Card class="surface-placeholder">
    <CardHeader class="surface-placeholder__header">
      <div>
        <p class="eyebrow">Superfície registrada</p>
        <CardTitle>{{ surface.title }}</CardTitle>
        <p class="surface-placeholder__subtitle">{{ surfaceSubtitle() }}</p>
      </div>
      <div class="surface-placeholder__badges">
        <Badge variant="outline">{{ surface.key }}</Badge>
        <Badge variant="outline">{{ surface.implemented ? 'implementada' : 'em preparação' }}</Badge>
      </div>
    </CardHeader>

    <CardContent class="surface-placeholder__content">
      <div class="surface-placeholder__anatomy">
        <Badge v-for="item in surface.anatomy" :key="item" variant="outline">{{ item }}</Badge>
      </div>

      <Separator />

      <div v-if="surface.kind === 'objective'" class="surface-preview surface-preview--objective">
        <div class="surface-preview__panel surface-preview__panel--statement">
          <p class="section-label">Estímulo</p>
          <strong>{{ exerciseTitle ?? 'Questão objetiva' }}</strong>
          <p>
            Trecho read-only com classificação objetiva. O usuário escolhe a melhor alternativa sem sair
            da Arena.
          </p>
        </div>
        <div class="surface-preview__options">
          <button v-for="choice in ['A', 'B', 'C', 'D']" :key="choice" type="button" class="surface-preview__choice">
            <span class="surface-preview__choice-label">Alternativa {{ choice }}</span>
            <span class="surface-preview__choice-copy">
              {{ choice === 'A' ? 'correta em leitura superficial' : 'distrator plausível' }}
            </span>
          </button>
        </div>
        <div class="surface-preview__panel surface-preview__panel--feedback">
          <p class="section-label">Saída esperada</p>
          <p>Gabarito objetivo, misconception tag e revisão com IA ancorada na regra de linguagem.</p>
        </div>
      </div>

      <div v-else-if="surface.kind === 'restricted'" class="surface-preview surface-preview--restricted">
        <div class="surface-preview__panel">
          <p class="section-label">Original</p>
          <div class="surface-preview__code">
            <span>snippet quebrado</span>
            <span>trecho bloqueado</span>
            <span>linhas editáveis</span>
          </div>
        </div>
        <div class="surface-preview__panel surface-preview__panel--center">
          <p class="section-label">Correção guiada</p>
          <div class="surface-preview__diff">
            <span>diff</span>
            <span>slots editáveis</span>
            <span>validação estrutural</span>
          </div>
        </div>
        <div class="surface-preview__panel">
          <p class="section-label">Feedback</p>
          <p>O corretor explica a menor mudança válida e o raciocínio por trás dela.</p>
        </div>
      </div>

      <div v-else-if="surface.kind === 'contract'" class="surface-preview surface-preview--contract">
        <div class="surface-preview__panel">
          <p class="section-label">Contrato</p>
          <div class="surface-preview__contract-grid">
            <div class="surface-preview__contract-box">
              <strong>Request</strong>
              <span>{{ sessionConfig?.family_key ?? 'family_key' }}</span>
            </div>
            <div class="surface-preview__contract-box">
              <strong>Response</strong>
              <span>{{ sessionConfig?.surface_key ?? surface.key }}</span>
            </div>
          </div>
        </div>
        <div class="surface-preview__panel">
          <p class="section-label">Observáveis</p>
          <p>Status code, schema, headers, preview e assertions visíveis para o aluno.</p>
        </div>
      </div>

      <div v-else class="surface-preview surface-preview--guided">
        <div class="surface-preview__panel">
          <p class="section-label">Prompt</p>
          <p>
            A resposta escrita é guiada por rubrica, contexto e revisão assistida por IA depois da tentativa.
          </p>
        </div>
        <div class="surface-preview__panel surface-preview__panel--textarea">
          <p class="section-label">Resposta</p>
          <div class="surface-preview__textarea">
            <span>Escreva sua justificativa aqui...</span>
          </div>
        </div>
        <div class="surface-preview__panel">
          <p class="section-label">Rubrica</p>
          <p>Critérios, pontos fortes, lacunas e próximos passos em uma visão estruturada.</p>
        </div>
      </div>
    </CardContent>
  </Card>
</template>

<style scoped>
.surface-placeholder {
  display: grid;
  grid-template-rows: auto 1fr;
  min-height: 0;
  height: 100%;
}

.surface-placeholder__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}

.surface-placeholder__subtitle {
  margin-top: 0.45rem;
  color: var(--muted);
  max-width: 52rem;
}

.surface-placeholder__badges,
.surface-placeholder__anatomy {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  justify-content: flex-end;
}

.surface-placeholder__content {
  display: grid;
  gap: 1rem;
  min-height: 0;
  overflow: auto;
}

.surface-preview {
  display: grid;
  gap: 1rem;
}

.surface-preview--objective,
.surface-preview--restricted,
.surface-preview--contract,
.surface-preview--guided {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.surface-preview__panel {
  padding: 1rem;
  border: 1.5px solid color-mix(in srgb, var(--border) 80%, transparent);
  border-radius: 1rem;
  background: color-mix(in srgb, var(--surface) 92%, var(--primary) 8%);
  display: grid;
  gap: 0.65rem;
  min-height: 9rem;
}

.surface-preview__panel--statement,
.surface-preview__panel--feedback,
.surface-preview__panel--textarea {
  background: color-mix(in srgb, var(--primary-container) 15%, var(--surface));
}

.surface-preview__options,
.surface-preview__contract-grid {
  display: grid;
  gap: 0.75rem;
}

.surface-preview__choice,
.surface-preview__contract-box {
  padding: 0.9rem 1rem;
  border-radius: 0.95rem;
  border: 1.5px solid color-mix(in srgb, var(--border) 70%, transparent);
  background: color-mix(in srgb, var(--surface) 90%, var(--primary) 10%);
  text-align: left;
}

.surface-preview__choice {
  display: grid;
  gap: 0.3rem;
}

.surface-preview__choice-label,
.surface-preview__contract-box strong {
  font-family: 'Space Grotesk', sans-serif;
  letter-spacing: 0.02em;
}

.surface-preview__choice-copy,
.surface-preview__contract-box span,
.surface-preview__textarea span {
  color: var(--muted);
}

.surface-preview__code,
.surface-preview__diff {
  display: grid;
  gap: 0.5rem;
  padding: 1rem;
  border-radius: 0.95rem;
  background: color-mix(in srgb, var(--surface) 86%, var(--primary) 14%);
  border: 1px dashed color-mix(in srgb, var(--primary) 35%, transparent);
}

.surface-preview__textarea {
  min-height: 8rem;
  padding: 1rem;
  border-radius: 0.95rem;
  border: 1px dashed color-mix(in srgb, var(--primary) 35%, transparent);
}

@media (max-width: 1120px) {
  .surface-preview--objective,
  .surface-preview--restricted,
  .surface-preview--contract,
  .surface-preview--guided {
    grid-template-columns: 1fr;
  }
}
</style>
