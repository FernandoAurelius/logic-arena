<script setup lang="ts">
import { computed, ref } from 'vue'
import { BookOpenText, ChevronRight, History, Rows3, PanelLeftClose, PanelLeftOpen, Undo2 } from 'lucide-vue-next'
import { TooltipArrow, TooltipContent, TooltipPortal, TooltipProvider, TooltipRoot as Tooltip, TooltipTrigger } from 'reka-ui'
import type { infer as ZodInfer } from 'zod'

import { schemas } from '@/lib/api/generated'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { ScrollArea } from '@/components/ui/scroll-area'

type ExerciseSummary = ZodInfer<typeof schemas.ExerciseSummarySchema>
type TrackExercise = ZodInfer<typeof schemas.TrackExerciseSchema>
type SubmissionSummary = ZodInfer<typeof schemas.SubmissionSummarySchema>

type GroupedExercise = {
  key: string
  label: string
  exercises: Array<ExerciseSummary | TrackExercise>
}

type SidebarSection = 'modulos' | 'historico'

const props = withDefaults(defineProps<{
  groupedExercises: GroupedExercise[]
  activeExerciseSlug?: string | null
  sidebarHistory: SubmissionSummary[]
  latestSubmissionId?: number | null
  routeTrackSlug?: string | null
  trackName?: string | null
  canGoPrevious?: boolean
  canGoNext?: boolean
}>(), {
  activeExerciseSlug: null,
  latestSubmissionId: null,
  routeTrackSlug: null,
  trackName: null,
  canGoPrevious: false,
  canGoNext: false,
})

const emit = defineEmits<{
  (event: 'select-exercise', slug: string): void
  (event: 'open-history', submission: SubmissionSummary): void
  (event: 'go-track'): void
  (event: 'go-navigator'): void
  (event: 'navigate-track', direction: 'previous' | 'next'): void
}>()

const expanded = ref(false)
const activeSection = ref<SidebarSection>('modulos')
const confirmNavigatorOpen = ref(false)

const totalExerciseCount = computed(() =>
  props.groupedExercises.reduce((total, group) => total + group.exercises.length, 0),
)

const panelTitle = computed(() => {
  if (props.routeTrackSlug) {
    return props.trackName ?? 'Trilha ativa'
  }
  return 'Arena'
})

function toggleSection(section: SidebarSection) {
  if (expanded.value && activeSection.value === section) {
    expanded.value = false
    return
  }

  activeSection.value = section
  expanded.value = true
}

function sidebarLabel(section: SidebarSection) {
  switch (section) {
    case 'modulos':
      return 'Módulos'
    case 'historico':
      return 'Histórico'
  }
}

function traduzirStatusExecucao(status?: string) {
  switch (status) {
    case 'passed':
      return 'Aprovada'
    case 'failed':
      return 'Reprovada'
    case 'error':
      return 'Erro'
    case 'pending':
      return 'Pendente'
    default:
      return 'Inativa'
  }
}

function openNavigatorConfirm() {
  confirmNavigatorOpen.value = true
}

function confirmGoNavigator() {
  confirmNavigatorOpen.value = false
  emit('go-navigator')
}
</script>

<template>
  <aside class="arena-sidebar" :data-expanded="expanded">
    <TooltipProvider :delay-duration="120">
      <div class="arena-sidebar-rail">
        <Tooltip>
          <TooltipTrigger as-child>
            <button
              class="arena-sidebar-toggle"
              type="button"
              :aria-label="expanded ? 'Recolher painel lateral' : 'Expandir painel lateral'"
              :title="expanded ? 'Recolher painel lateral' : 'Expandir painel lateral'"
              @click="expanded = !expanded"
            >
              <PanelLeftClose v-if="expanded" :size="18" />
              <PanelLeftOpen v-else :size="18" />
            </button>
          </TooltipTrigger>
          <TooltipPortal>
            <TooltipContent class="logic-tooltip-content" :side-offset="10" side="right">
              {{ expanded ? 'Recolher painel lateral' : 'Expandir painel lateral' }}
              <TooltipArrow class="logic-tooltip-arrow" :width="10" :height="6" />
            </TooltipContent>
          </TooltipPortal>
        </Tooltip>

        <div class="arena-sidebar-rail__sections">
          <Tooltip>
            <TooltipTrigger as-child>
              <button
                class="arena-sidebar-rail__button"
                :class="{ active: expanded && activeSection === 'modulos' }"
                type="button"
                aria-label="Abrir módulos"
                title="Módulos"
                @click="toggleSection('modulos')"
              >
                <Rows3 :size="18" />
              </button>
            </TooltipTrigger>
            <TooltipPortal>
              <TooltipContent class="logic-tooltip-content" :side-offset="10" side="right">
                Módulos
                <TooltipArrow class="logic-tooltip-arrow" :width="10" :height="6" />
              </TooltipContent>
            </TooltipPortal>
          </Tooltip>

          <Tooltip>
            <TooltipTrigger as-child>
              <button
                class="arena-sidebar-rail__button"
                :class="{ active: expanded && activeSection === 'historico' }"
                type="button"
                aria-label="Abrir histórico"
                title="Histórico"
                @click="toggleSection('historico')"
              >
                <History :size="18" />
              </button>
            </TooltipTrigger>
            <TooltipPortal>
              <TooltipContent class="logic-tooltip-content" :side-offset="10" side="right">
                Histórico
                <TooltipArrow class="logic-tooltip-arrow" :width="10" :height="6" />
              </TooltipContent>
            </TooltipPortal>
          </Tooltip>
        </div>

        <div class="arena-sidebar-rail__actions">
          <Tooltip v-if="routeTrackSlug">
            <TooltipTrigger as-child>
              <button
                class="arena-sidebar-rail__button"
                type="button"
                aria-label="Voltar para trilha"
                title="Voltar para trilha"
                @click="emit('go-track')"
              >
                <BookOpenText :size="18" />
              </button>
            </TooltipTrigger>
            <TooltipPortal>
              <TooltipContent class="logic-tooltip-content" :side-offset="10" side="right">
                Voltar para trilha
                <TooltipArrow class="logic-tooltip-arrow" :width="10" :height="6" />
              </TooltipContent>
            </TooltipPortal>
          </Tooltip>

          <Tooltip v-if="routeTrackSlug">
            <TooltipTrigger v-if="canGoPrevious" as-child>
              <button
                class="arena-sidebar-rail__button"
                type="button"
                aria-label="Exercício anterior"
                title="Exercício anterior"
                @click="emit('navigate-track', 'previous')"
              >
                <ChevronRight :size="18" class="track-arrow--prev" />
              </button>
            </TooltipTrigger>
            <TooltipTrigger v-else as-child>
              <span class="arena-sidebar-rail__button arena-sidebar-rail__button--disabled" aria-hidden="true">
                <button
                  class="arena-sidebar-rail__button"
                  type="button"
                  aria-label="Exercício anterior"
                  title="Exercício anterior"
                  disabled
                >
                  <ChevronRight :size="18" class="track-arrow--prev" />
                </button>
              </span>
            </TooltipTrigger>
            <TooltipPortal>
              <TooltipContent class="logic-tooltip-content" :side-offset="10" side="right">
                Exercício anterior
                <TooltipArrow class="logic-tooltip-arrow" :width="10" :height="6" />
              </TooltipContent>
            </TooltipPortal>
          </Tooltip>

          <Tooltip v-if="routeTrackSlug">
            <TooltipTrigger v-if="canGoNext" as-child>
              <button
                class="arena-sidebar-rail__button"
                type="button"
                aria-label="Próximo exercício"
                title="Próximo exercício"
                @click="emit('navigate-track', 'next')"
              >
                <ChevronRight :size="18" />
              </button>
            </TooltipTrigger>
            <TooltipTrigger v-else as-child>
              <span class="arena-sidebar-rail__button arena-sidebar-rail__button--disabled" aria-hidden="true">
                <button
                  class="arena-sidebar-rail__button"
                  type="button"
                  aria-label="Próximo exercício"
                  title="Próximo exercício"
                  disabled
                >
                  <ChevronRight :size="18" />
                </button>
              </span>
            </TooltipTrigger>
            <TooltipPortal>
              <TooltipContent class="logic-tooltip-content" :side-offset="10" side="right">
                Próximo exercício
                <TooltipArrow class="logic-tooltip-arrow" :width="10" :height="6" />
              </TooltipContent>
            </TooltipPortal>
          </Tooltip>

          <Tooltip>
            <TooltipTrigger as-child>
              <button
                class="arena-sidebar-rail__button"
                type="button"
                aria-label="Voltar ao navegador"
                title="Voltar ao navegador"
                @click="openNavigatorConfirm"
              >
                <Undo2 :size="18" />
              </button>
            </TooltipTrigger>
            <TooltipPortal>
              <TooltipContent class="logic-tooltip-content" :side-offset="10" side="right">
                Voltar ao navegador
                <TooltipArrow class="logic-tooltip-arrow" :width="10" :height="6" />
              </TooltipContent>
            </TooltipPortal>
          </Tooltip>
        </div>
      </div>
    </TooltipProvider>

    <Dialog :open="confirmNavigatorOpen" @update:open="confirmNavigatorOpen = $event">
      <DialogContent class="arena-confirm-dialog">
        <DialogHeader>
          <DialogTitle>Voltar ao navegador</DialogTitle>
          <DialogDescription>
            Você vai sair da questão atual e retornar para a visão geral da arena.
          </DialogDescription>
        </DialogHeader>
        <div class="arena-confirm-dialog__actions">
          <Button variant="outline" size="sm" @click="confirmNavigatorOpen = false">
            Cancelar
          </Button>
          <Button size="sm" @click="confirmGoNavigator">
            Confirmar saída
          </Button>
        </div>
      </DialogContent>
    </Dialog>

    <transition name="arena-sidebar-panel">
      <div v-if="expanded" class="arena-sidebar-panel">
        <div class="arena-sidebar-panel__header">
          <div>
            <p class="eyebrow">{{ sidebarLabel(activeSection) }}</p>
            <h3>{{ panelTitle }}</h3>
          </div>
          <small v-if="activeSection === 'modulos'">{{ totalExerciseCount }} exercícios</small>
        </div>

        <ScrollArea class="arena-sidebar-panel__scroll" viewport-class="arena-sidebar-panel__viewport">
          <div v-if="activeSection === 'modulos'" class="arena-sidebar-panel__stack">
            <Card class="module-panel module-panel--embedded">
              <CardHeader>
                <CardTitle>Módulos</CardTitle>
                <CardDescription>Selecione a questão atual da rodada.</CardDescription>
              </CardHeader>
              <CardContent class="module-list">
                <div v-for="group in groupedExercises" :key="group.key" class="module-group">
                  <div class="module-group-heading">
                    <span>{{ group.label }}</span>
                    <small>{{ group.exercises.length }} exercícios</small>
                  </div>
                  <button
                    v-for="exercise in group.exercises"
                    :key="exercise.slug"
                    class="module-link"
                    :class="{ active: activeExerciseSlug === exercise.slug }"
                    @click="emit('select-exercise', exercise.slug)"
                  >
                    <div>
                      <strong>{{ exercise.title }}</strong>
                      <small>
                        {{
                          'position' in exercise
                            ? `Etapa ${exercise.position} · ${exercise.estimated_time_minutes} min`
                            : `${exercise.track_name ?? 'Trilha livre'} · ${exercise.difficulty}`
                        }}
                      </small>
                    </div>
                  </button>
                </div>
              </CardContent>
            </Card>
          </div>

          <div v-else-if="activeSection === 'historico'" class="arena-sidebar-panel__stack">
            <Card class="history-panel history-panel--embedded">
              <CardHeader>
                <CardTitle>Histórico</CardTitle>
                <CardDescription>Últimas execuções persistidas por exercício.</CardDescription>
              </CardHeader>
              <CardContent>
                <ul class="history-list">
                  <li v-for="submission in sidebarHistory" :key="submission.id">
                    <button
                      class="history-entry"
                      :class="{ active: latestSubmissionId === submission.id }"
                      @click="emit('open-history', submission)"
                    >
                      <div class="history-line">
                        <strong>{{ submission.exercise_title }}</strong>
                        <Badge :variant="submission.status === 'passed' ? 'default' : 'outline'">
                          {{ traduzirStatusExecucao(submission.status) }}
                        </Badge>
                      </div>
                      <span>{{ submission.passed_tests }}/{{ submission.total_tests }} testes</span>
                    </button>
                  </li>
                  <li v-if="sidebarHistory.length === 0" class="dimmed">Nenhuma execução persistida.</li>
                </ul>
              </CardContent>
            </Card>
          </div>

        </ScrollArea>
      </div>
    </transition>
  </aside>
</template>
