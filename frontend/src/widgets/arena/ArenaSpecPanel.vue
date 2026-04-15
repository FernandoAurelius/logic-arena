<script setup lang="ts">
import { ChevronRight, FileText, FlaskConical, ListChecks } from 'lucide-vue-next'

import { Badge } from '@/shared/ui/badge'
import { Card, CardContent, CardHeader } from '@/shared/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/shared/ui/tabs'
import type { SessionConfig } from '@/entities/practice-session'

type VisibleTestCase = {
  id: number
  input_data: string
  expected_output: string
}

defineProps<{
  specTab: 'descricao' | 'exemplos' | 'testes'
  routeTrackSlug?: string | null
  sessionConfig?: SessionConfig | null
  activeExercise?: {
    title: string
    statement: string
    module_name?: string | null
    track_name?: string | null
    difficulty: string
    sample_input: string
    sample_output: string
  } | null
  activeIndex: number
  exerciseCount: number
  isSubmitting: boolean
  isBooting: boolean
  trackName?: string | null
  activeTrackIndex: number
  trackExerciseCount: number
  activeTrackBrief?: string | null
  visibleTestCases: VisibleTestCase[]
}>()

const emit = defineEmits<{
  (event: 'update:specTab', value: 'descricao' | 'exemplos' | 'testes'): void
  (event: 'go-navigator'): void
  (event: 'go-track'): void
}>()

function handleSpecTabChange(value: string | number) {
  if (value === 'descricao' || value === 'exemplos' || value === 'testes') {
    emit('update:specTab', value)
  }
}

function traduzirEstadoArena(isSubmitting: boolean, isBooting: boolean) {
  if (isSubmitting) return 'Executando'
  if (isBooting) return 'Carregando'
  return 'Pronta'
}

function formatSampleBlock(text: string) {
  const normalized = text.replace(/\r/g, '').trim()
  if (!normalized) return ['Sem exemplo disponível.']
  return normalized.split('\n')
}
</script>

<template>
  <Card class="spec-card">
    <CardHeader class="spec-card-header">
      <Tabs :model-value="specTab" class="spec-tabs" @update:model-value="handleSpecTabChange">
        <TabsList class="spec-tabs-list">
          <TabsTrigger value="descricao" class="spec-tabs-trigger">
            <FileText :size="15" />
            Especificação
          </TabsTrigger>
          <TabsTrigger value="exemplos" class="spec-tabs-trigger">
            <FlaskConical :size="15" />
            Exemplos
          </TabsTrigger>
          <TabsTrigger value="testes" class="spec-tabs-trigger">
            <ListChecks :size="15" />
            Testes
          </TabsTrigger>
        </TabsList>
      </Tabs>
      <div class="spec-heading-block">
        <div class="breadcrumb">
          <button class="breadcrumb-link" type="button" @click="$emit('go-navigator')">Navegador</button>
          <ChevronRight :size="14" />
          <button
            v-if="routeTrackSlug"
            class="breadcrumb-link"
            type="button"
            @click="$emit('go-track')"
          >
            {{ activeExercise?.track_name ?? 'Trilha' }}
          </button>
          <template v-if="routeTrackSlug">
            <ChevronRight :size="14" />
          </template>
          <button
            v-else-if="activeExercise?.module_name"
            class="breadcrumb-link"
            type="button"
            @click="$emit('go-navigator')"
          >
            {{ activeExercise.module_name }}
          </button>
          <template v-if="!routeTrackSlug && activeExercise?.module_name">
            <ChevronRight :size="14" />
          </template>
          <span class="active">{{ activeExercise?.difficulty ?? 'Exercício' }}</span>
        </div>
        <h1 class="spec-heading-title">{{ activeExercise?.title ?? 'Aguardando exercício' }}</h1>
        <div class="challenge-meta challenge-meta--compact">
          <Badge variant="outline">{{ activeExercise?.module_name ?? 'Sem módulo' }}</Badge>
          <Badge variant="outline">{{ activeExercise?.track_name ?? 'Sem trilha' }}</Badge>
          <Badge variant="outline">{{ activeExercise?.difficulty ?? 'Exercício' }}</Badge>
          <Badge variant="outline">{{ sessionConfig?.family_key ?? 'code_lab' }}</Badge>
          <Badge variant="outline">{{ sessionConfig?.surface_key ?? 'code_editor_single' }}</Badge>
          <Badge variant="outline">{{ sessionConfig?.mode ?? 'practice' }}</Badge>
          <Badge variant="outline">Questão {{ activeIndex }}/{{ exerciseCount || 1 }}</Badge>
          <Badge :variant="isSubmitting || isBooting ? 'dark' : 'default'">
            {{ traduzirEstadoArena(isSubmitting, isBooting) }}
          </Badge>
        </div>
        <div v-if="routeTrackSlug && trackName" class="workspace-track-inline">
          <span class="workspace-track-inline__label">
            {{ trackName }}
            <small>
              {{
                activeTrackIndex >= 0
                  ? `Etapa ${activeTrackIndex + 1} de ${trackExerciseCount}`
                  : 'Contexto de trilha ativo'
              }}
            </small>
          </span>
        </div>
      </div>
    </CardHeader>
    <CardContent class="spec-content">
      <Tabs :model-value="specTab" class="spec-tabs-content" @update:model-value="handleSpecTabChange">
        <TabsContent value="descricao" class="spec-pane">
          <div class="formula-box formula-box--statement">
            <p class="section-label">Enunciado</p>
            <p>{{ activeExercise?.statement }}</p>
          </div>

          <div class="formula-box">
            <p class="section-label">Fluxo canônico</p>
            <strong>
              {{ sessionConfig?.family_key ?? 'code_lab' }} · {{ sessionConfig?.surface_key ?? 'code_editor_single' }}
            </strong>
            <p>
              A Arena abre uma sessão canônica, recebe snapshots de execução e consolida avaliação e revisão
              como contratos explícitos da tentativa.
            </p>
          </div>

          <div class="formula-box">
            <p class="section-label">Modo de prova</p>
            <strong>Resolva sem código inicial. Abra <em>dicas</em> apenas se quiser uma pista opcional.</strong>
          </div>

          <div v-if="routeTrackSlug && trackName && activeTrackIndex >= 0" class="formula-box formula-box--track">
            <p class="section-label">Posição na trilha</p>
            <strong>{{ trackName }} · etapa {{ activeTrackIndex + 1 }}</strong>
            <p>
              {{ activeTrackBrief ?? 'Este exercício faz parte de um percurso estruturado de progressão.' }}
            </p>
          </div>
        </TabsContent>

        <TabsContent value="exemplos" class="spec-pane spec-pane--examples">
          <div class="example-flow-grid">
            <div class="example-flow-card io-card">
              <p class="section-label">Exemplo de entrada</p>
              <div class="code-block">
                <span v-for="(line, index) in formatSampleBlock(activeExercise?.sample_input ?? '')" :key="`input-${index}`">{{ line }}</span>
              </div>
            </div>
            <div class="example-flow-arrow" aria-hidden="true">
              <ChevronRight :size="18" />
            </div>
            <div class="example-flow-card io-card">
              <p class="section-label">Exemplo de saída</p>
              <div class="code-block">
                <span v-for="(line, index) in formatSampleBlock(activeExercise?.sample_output ?? '')" :key="`output-${index}`">{{ line }}</span>
              </div>
            </div>
          </div>
        </TabsContent>

        <TabsContent value="testes" class="spec-pane">
          <div v-if="visibleTestCases.length" class="visible-tests">
            <p class="section-label">Testes</p>
            <div class="test-grid">
              <div v-for="testCase in visibleTestCases" :key="testCase.id" class="test-card">
                <strong>Teste {{ testCase.id }}</strong>
                <div class="test-case-line">
                  <span>Entrada</span>
                  <code>{{ testCase.input_data }}</code>
                </div>
                <div class="test-case-line">
                  <span>Saída</span>
                  <code>{{ testCase.expected_output }}</code>
                </div>
              </div>
            </div>
          </div>
          <div v-else class="formula-box">
            <p class="section-label">Testes</p>
            <p>Este exercício não expõe testes visíveis nesta rodada.</p>
          </div>
        </TabsContent>
      </Tabs>
    </CardContent>
  </Card>
</template>
