<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowRight, BookOpenText, Lock, LogOut, Play, Route, ShieldCheck, UserRound } from 'lucide-vue-next'
import type { infer as ZodInfer } from 'zod'

import { catalogApi } from '@/lib/api/client'
import { schemas } from '@/lib/api/generated'
import { useSession } from '@/lib/session'
import ProfileModal from '@/components/theme/ProfileModal.vue'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Drawer, DrawerContent, DrawerDescription, DrawerHeader, DrawerTitle } from '@/components/ui/drawer'

type TrackDetail = ZodInfer<typeof schemas.TrackDetailSchema>
type TrackExercise = ZodInfer<typeof schemas.TrackExerciseSchema>
type TrackNodeLayout = {
  exercise: TrackExercise
  side: 'left' | 'right'
  anchorX: number
  anchorY: number
  calloutX: number
  calloutY: number
}
type TrackTipLayout = {
  title: string
  copy: string
  x: number
  y: number
  pathD: string
  status: string
}
type TrackUnitLayout = {
  label: string
  x: number
  y: number
}

const MAP_WIDTH = 1080
const MAP_CALLOUT_WIDTH = 258
const MAP_CALLOUT_HEIGHT = 116
const MAP_TIP_WIDTH = 220
const MAP_TIP_HEIGHT = 112
const MAP_TIP_GAP_X = 52
const MAP_TIP_GAP_Y = 34
const MAP_TOP_PADDING = 90
const MAP_ROW_GAP = 206
const MILESTONE_CARD_WIDTH = 408
const MILESTONE_CARD_HEIGHT = 132

const route = useRoute()
const router = useRouter()
const session = useSession()

const track = ref<TrackDetail | null>(null)
const selectedExerciseSlug = ref<string>('')
const loading = ref(false)
const errorMessage = ref('')
const showProfile = ref(false)
const drawerOpen = ref(false)

const orderedExercises = computed(() => track.value?.exercises ?? [])
const selectedExercise = computed<TrackExercise | null>(() => {
  if (!track.value) return null
  return orderedExercises.value.find((exercise) => exercise.slug === selectedExerciseSlug.value) ?? orderedExercises.value[0] ?? null
})
const selectedExerciseIndex = computed(() => {
  if (!selectedExercise.value) return -1
  return orderedExercises.value.findIndex((exercise) => exercise.slug === selectedExercise.value?.slug)
})
const previousExercise = computed(() => {
  if (selectedExerciseIndex.value <= 0) return null
  return orderedExercises.value[selectedExerciseIndex.value - 1] ?? null
})
const nextExercise = computed(() => {
  if (selectedExerciseIndex.value < 0) return null
  return orderedExercises.value[selectedExerciseIndex.value + 1] ?? null
})

type Rect = {
  x: number
  y: number
  width: number
  height: number
}

function rectsOverlap(a: Rect, b: Rect, gap = 0) {
  return !(
    a.x + a.width + gap <= b.x ||
    b.x + b.width + gap <= a.x ||
    a.y + a.height + gap <= b.y ||
    b.y + b.height + gap <= a.y
  )
}

function clampRect(rect: Rect): Rect {
  return {
    ...rect,
    x: Math.max(24, Math.min(MAP_WIDTH - rect.width - 24, rect.x)),
    y: Math.max(20, rect.y),
  }
}

function buildTipPath(callout: Rect, tip: Rect) {
  const tipOnLeft = tip.x + tip.width / 2 < callout.x + callout.width / 2
  const tipAbove = tip.y + tip.height / 2 < callout.y + callout.height / 2
  const startX = tipOnLeft ? callout.x : callout.x + callout.width
  const startY = tipAbove ? callout.y + 16 : callout.y + callout.height - 16
  const endX = tipOnLeft ? tip.x + tip.width - 18 : tip.x + 18
  const endY = tipAbove ? tip.y + tip.height - 18 : tip.y + 18
  const midX = tipOnLeft ? startX - 30 : startX + 30

  return `M ${startX} ${startY} C ${midX} ${startY} ${midX} ${endY} ${endX} ${endY}`
}

const roadmapCurveOffsets = [-148, 122, -102, 152, -124, 104, -86, 132]
const trackNodeLayouts = computed<TrackNodeLayout[]>(() =>
  orderedExercises.value.map((exercise, index) => {
    const side = index % 2 === 0 ? 'left' : 'right'
    const anchorY = MAP_TOP_PADDING + index * MAP_ROW_GAP
    const anchorX = MAP_WIDTH / 2 + roadmapCurveOffsets[index % roadmapCurveOffsets.length]
    const calloutXBase = side === 'left' ? anchorX - MAP_CALLOUT_WIDTH - 72 : anchorX + 72
    const calloutX = Math.max(30, Math.min(MAP_WIDTH - MAP_CALLOUT_WIDTH - 30, calloutXBase))
    const calloutY = anchorY - MAP_CALLOUT_HEIGHT / 2

    return {
      exercise,
      side,
      anchorX,
      anchorY,
      calloutX,
      calloutY,
    }
  }),
)
const roadmapUnits = computed<TrackUnitLayout[]>(() =>
  trackNodeLayouts.value
    .filter((_, index) => index % 3 === 0)
    .map((layout, index) => ({
      label: `Unidade ${String(index + 1).padStart(2, '0')}`,
      x: layout.side === 'left' ? 110 : MAP_WIDTH - 110 - 132,
      y: layout.anchorY - 82,
    })),
)
const roadmapTips = computed<TrackTipLayout[]>(() => {
  const source = [
    ...(track.value?.concepts.map((concept) => ({
      title: concept.title,
      copy: concept.summary,
    })) ?? []),
    ...((track.value?.prerequisites ?? []).map((item) => ({
      title: 'Fundamento-chave',
      copy: item,
    }))),
  ].slice(0, 3)

  const placedTips: Rect[] = []

  return source.map((tip, index) => {
    const current = trackNodeLayouts.value[index]
    if (!current) {
      return {
        ...tip,
        x: 88,
        y: MAP_TOP_PADDING + index * 200 + 80,
        pathD: '',
        status: 'locked',
      }
    }

    const calloutRect: Rect = {
      x: current.calloutX,
      y: current.calloutY,
      width: MAP_CALLOUT_WIDTH,
      height: MAP_CALLOUT_HEIGHT,
    }

    const centeredX = calloutRect.x + (calloutRect.width - MAP_TIP_WIDTH) / 2
    const preferredCandidates: Rect[] = [
      { x: centeredX, y: calloutRect.y + calloutRect.height + MAP_TIP_GAP_Y, width: MAP_TIP_WIDTH, height: MAP_TIP_HEIGHT },
      { x: centeredX, y: calloutRect.y - MAP_TIP_HEIGHT - (MAP_TIP_GAP_Y + 8), width: MAP_TIP_WIDTH, height: MAP_TIP_HEIGHT },
      current.side === 'left'
        ? { x: calloutRect.x - MAP_TIP_WIDTH - MAP_TIP_GAP_X, y: calloutRect.y + calloutRect.height + MAP_TIP_GAP_Y, width: MAP_TIP_WIDTH, height: MAP_TIP_HEIGHT }
        : { x: calloutRect.x + calloutRect.width + MAP_TIP_GAP_X, y: calloutRect.y + calloutRect.height + MAP_TIP_GAP_Y, width: MAP_TIP_WIDTH, height: MAP_TIP_HEIGHT },
      current.side === 'left'
        ? { x: calloutRect.x - MAP_TIP_WIDTH - MAP_TIP_GAP_X, y: calloutRect.y - MAP_TIP_HEIGHT - (MAP_TIP_GAP_Y + 8), width: MAP_TIP_WIDTH, height: MAP_TIP_HEIGHT }
        : { x: calloutRect.x + calloutRect.width + MAP_TIP_GAP_X, y: calloutRect.y - MAP_TIP_HEIGHT - (MAP_TIP_GAP_Y + 8), width: MAP_TIP_WIDTH, height: MAP_TIP_HEIGHT },
      current.side === 'left'
        ? { x: calloutRect.x + calloutRect.width + MAP_TIP_GAP_X, y: calloutRect.y + calloutRect.height + MAP_TIP_GAP_Y, width: MAP_TIP_WIDTH, height: MAP_TIP_HEIGHT }
        : { x: calloutRect.x - MAP_TIP_WIDTH - MAP_TIP_GAP_X, y: calloutRect.y + calloutRect.height + MAP_TIP_GAP_Y, width: MAP_TIP_WIDTH, height: MAP_TIP_HEIGHT },
      current.side === 'left'
        ? { x: calloutRect.x + calloutRect.width + MAP_TIP_GAP_X, y: calloutRect.y - MAP_TIP_HEIGHT - (MAP_TIP_GAP_Y + 8), width: MAP_TIP_WIDTH, height: MAP_TIP_HEIGHT }
        : { x: calloutRect.x - MAP_TIP_WIDTH - MAP_TIP_GAP_X, y: calloutRect.y - MAP_TIP_HEIGHT - (MAP_TIP_GAP_Y + 8), width: MAP_TIP_WIDTH, height: MAP_TIP_HEIGHT },
    ]

    const candidate = preferredCandidates
      .map(clampRect)
      .find((rect) =>
        !rectsOverlap(rect, calloutRect, 18) &&
        placedTips.every((placed) => !rectsOverlap(rect, placed, 18)),
      ) ?? clampRect(preferredCandidates[0]!)

    placedTips.push(candidate)

    return {
      ...tip,
      x: candidate.x,
      y: candidate.y,
      pathD: buildTipPath(calloutRect, candidate),
      status: current.exercise.progress.status,
    }
  })
})
const milestoneLayout = computed(() => {
  const lastY = trackNodeLayouts.value.at(-1)?.anchorY ?? MAP_TOP_PADDING
  const anchorY = lastY + 168
  const anchorX = MAP_WIDTH / 2 + 8
  const cardX = MAP_WIDTH / 2 - MILESTONE_CARD_WIDTH / 2
  const cardY = anchorY - 24
  return {
    anchorX,
    anchorY,
    cardX,
    cardY,
    cardWidth: MILESTONE_CARD_WIDTH,
    cardHeight: MILESTONE_CARD_HEIGHT,
  }
})
const roadmapHeight = computed(() => milestoneLayout.value.cardY + milestoneLayout.value.cardHeight + 72)
const roadmapViewBox = computed(() => `0 0 ${MAP_WIDTH} ${roadmapHeight.value}`)
const roadmapPath = computed(() => {
  const points = trackNodeLayouts.value.map((item) => ({ x: item.anchorX, y: item.anchorY }))
  points.push({ x: milestoneLayout.value.anchorX, y: milestoneLayout.value.anchorY })
  if (points.length === 0) return ''
  let path = `M ${points[0].x} ${points[0].y}`
  for (let index = 1; index < points.length; index += 1) {
    const previous = points[index - 1]
    const current = points[index]
    const midY = previous.y + (current.y - previous.y) / 2
    path += ` C ${previous.x} ${midY} ${current.x} ${midY} ${current.x} ${current.y}`
  }
  return path
})

function statusLabel(status: string) {
  if (status === 'passed') return 'Concluído'
  if (status === 'in_progress') return 'Em andamento'
  if (status === 'available') return 'Não iniciado'
  return 'Bloqueado'
}

function cardStyle(layout: TrackNodeLayout) {
  return {
    left: `${layout.calloutX}px`,
    top: `${layout.calloutY}px`,
    width: `${MAP_CALLOUT_WIDTH}px`,
  }
}

function tipStyle(tip: TrackTipLayout) {
  return {
    left: `${tip.x}px`,
    top: `${tip.y}px`,
  }
}

function unitStyle(unit: TrackUnitLayout) {
  return {
    left: `${unit.x}px`,
    top: `${unit.y}px`,
  }
}

function openExercisePanel(slug: string) {
  selectedExerciseSlug.value = slug
  drawerOpen.value = true
}

function openDidacticPanel() {
  const targetSlug = selectedExercise.value?.slug ?? track.value?.current_target_slug ?? orderedExercises.value[0]?.slug
  if (targetSlug) {
    void router.push({
      name: 'track-explanation',
      params: {
        trackSlug: track.value?.slug,
        exerciseSlug: targetSlug,
      },
    })
  }
}

function closeExercisePanel() {
  drawerOpen.value = false
}

function goToPreviousExercise() {
  if (previousExercise.value) {
    openExercisePanel(previousExercise.value.slug)
  }
}

function goToNextExercise() {
  if (nextExercise.value) {
    openExercisePanel(nextExercise.value.slug)
  }
}

function openArena(slug?: string) {
  void router.push({
    name: 'arena',
    query: slug ? { exercise: slug, track: track.value?.slug } : { track: track.value?.slug },
  })
}

async function loadTrack() {
  loading.value = true
  errorMessage.value = ''

  try {
    const response = await catalogApi.get('/api/catalog/tracks/:track_slug', {
      params: { track_slug: route.params.trackSlug as string },
      headers: { authorization: session.authHeader() ?? undefined },
    })
    track.value = response
    selectedExerciseSlug.value = response.current_target_slug ?? response.exercises[0]?.slug ?? ''
  } catch (error) {
    console.error(error)
    errorMessage.value = 'Não foi possível carregar essa trilha.'
  } finally {
    loading.value = false
  }
}

async function logout() {
  session.clearSession()
  await router.push({ name: 'landing' })
}

onMounted(() => {
  void loadTrack()
})

watch(
  () => route.params.trackSlug,
  () => {
    void loadTrack()
  },
)
</script>

<template>
  <div class="track-page">
    <header class="topbar">
      <div class="topbar-left topbar-left--nav">
        <span class="brand-wordmark">LOGIC ARENA</span>
        <nav class="workspace-nav">
          <button class="workspace-nav-link" type="button" @click="router.push({ name: 'navigator' })">Navegador</button>
          <button class="workspace-nav-link" type="button" @click="router.push({ name: 'arena' })">Arena</button>
          <button class="workspace-nav-link workspace-nav-link--active" type="button">Trilha</button>
        </nav>
      </div>
      <div class="topbar-right">
        <div class="topbar-actions">
          <Button variant="outline" size="sm" @click="showProfile = true">
            <UserRound :size="14" />
            Perfil
          </Button>
          <Button variant="outline" size="sm" @click="logout">
            <LogOut :size="14" />
            Sair
          </Button>
        </div>
        <div class="topbar-status">
          <div class="level-box">
            <strong>NÍVEL {{ session.currentUser.value?.level ?? 1 }}</strong>
            <span>{{ session.currentUser.value?.nickname ?? 'operador' }}</span>
            <small>{{ session.currentUser.value?.xp_total ?? 0 }} XP totais</small>
          </div>
        </div>
      </div>
    </header>

    <main class="track-workspace">
      <div class="track-shell">
        <p v-if="errorMessage" class="notice error">{{ errorMessage }}</p>
        <div v-else-if="loading" class="navigator-empty-state">
          <BookOpenText :size="18" />
          <span>Carregando mapa da trilha...</span>
        </div>

        <div v-else-if="track" class="track-content-grid">
          <section class="track-roadmap-panel">
            <div class="track-roadmap-grid">
              <div class="track-map-stage">
                <aside class="track-map-foundations">
                  <div class="track-map-foundations-title">
                    <p class="eyebrow">Fundamentos</p>
                    <h2>Base da trilha</h2>
                  </div>

                  <Card class="track-summary-card">
                    <CardHeader>
                      <p class="eyebrow">Trilha atual</p>
                      <CardTitle>{{ track.name }}</CardTitle>
                      <CardDescription>{{ track.level_label }}</CardDescription>
                    </CardHeader>
                    <CardContent class="track-summary-body">
                      <strong class="track-summary-progress">{{ track.progress_percent }}%</strong>
                      <div class="navigator-progress-rail">
                        <div class="navigator-progress-rail-fill" :style="{ width: `${track.progress_percent}%` }"></div>
                      </div>
                      <p class="track-summary-copy">{{ track.goal }}</p>
                      <div class="track-summary-stats">
                        <div>
                          <small class="eyebrow">Módulos</small>
                          <strong>{{ track.completed_exercises }}/{{ track.total_exercises }}</strong>
                        </div>
                        <div>
                          <small class="eyebrow">Alvo</small>
                          <strong>{{ track.current_target_title ?? 'Masterizado' }}</strong>
                        </div>
                      </div>
                      <div class="track-summary-actions">
                        <Button variant="outline" class="w-full" @click="router.push({ name: 'navigator' })">
                          <Route :size="16" />
                          Voltar ao Navegador
                        </Button>
                        <Button class="w-full" @click="openArena(track?.current_target_slug ?? selectedExercise?.slug)">
                          <Play :size="16" />
                          Continuar na Arena
                        </Button>
                        <Button variant="outline" class="w-full" @click="openDidacticPanel">
                          <BookOpenText :size="16" />
                          Aprofundamento Didático
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                </aside>

                <div class="track-map-canvas">
                  <div class="track-map-shell" :style="{ minHeight: `${roadmapHeight}px` }">
                    <svg class="track-map-svg" :viewBox="roadmapViewBox" preserveAspectRatio="xMidYMin meet" aria-hidden="true">
                      <path class="track-map-path" :d="roadmapPath" />
                      <path
                        v-for="tip in roadmapTips"
                        :key="`${tip.title}-${tip.y}-path`"
                        class="track-map-tip-path"
                        :d="tip.pathD"
                      />
                    </svg>

                    <div
                      v-for="unit in roadmapUnits"
                      :key="unit.label"
                      class="track-map-unit"
                      :style="unitStyle(unit)"
                    >
                      {{ unit.label }}
                    </div>

                    <button
                      v-for="layout in trackNodeLayouts"
                      :key="`${layout.exercise.slug}-stop`"
                      class="track-map-stop"
                      :class="[
                        `track-map-stop--${layout.exercise.progress.status}`,
                        { 'track-map-stop--current': layout.exercise.is_current_target },
                        { 'track-map-stop--selected': selectedExercise?.slug === layout.exercise.slug },
                      ]"
                      :style="{ left: `${layout.anchorX}px`, top: `${layout.anchorY}px` }"
                      type="button"
                      @click="openExercisePanel(layout.exercise.slug)"
                    >
                      <span class="track-map-stop-ring">
                        <span class="track-map-stop-core">
                          <span class="track-map-stop-label">{{ layout.exercise.position }}</span>
                        </span>
                      </span>
                    </button>

                    <article
                      v-for="layout in trackNodeLayouts"
                      :key="`${layout.exercise.slug}-callout`"
                      class="track-map-callout"
                      :class="[
                        `track-map-callout--${layout.exercise.progress.status}`,
                        { 'track-map-callout--selected': selectedExercise?.slug === layout.exercise.slug },
                        { 'track-map-callout--current': layout.exercise.is_current_target },
                      ]"
                      :style="cardStyle(layout)"
                    >
                      <button class="track-map-callout-hit" type="button" @click="openExercisePanel(layout.exercise.slug)">
                        <div class="track-map-callout-head">
                          <span class="track-status-badge" :class="`track-status-badge--${layout.exercise.progress.status}`">
                            {{ statusLabel(layout.exercise.progress.status) }}
                          </span>
                          <span class="track-step-index">ETAPA {{ layout.exercise.position }}</span>
                        </div>
                        <strong>{{ layout.exercise.title }}</strong>
                        <p>{{ layout.exercise.exercise_type_label }} · {{ layout.exercise.estimated_time_minutes }} min</p>
                      </button>
                    </article>

                    <article
                      class="track-milestone-card track-map-milestone-card"
                      :class="{ 'track-milestone-card--locked': !track.milestone.unlocked }"
                      :style="{ left: `${milestoneLayout.cardX}px`, top: `${milestoneLayout.cardY}px`, width: `${milestoneLayout.cardWidth}px` }"
                    >
                      <div class="track-milestone-icon">
                        <ShieldCheck v-if="track.milestone.unlocked" :size="18" />
                        <Lock v-else :size="18" />
                      </div>
                      <div>
                        <p class="eyebrow">Marco de progresso</p>
                        <h3>{{ track.milestone.title }}</h3>
                        <p>{{ track.milestone.summary }}</p>
                        <small>
                            {{ track.milestone.unlocked ? 'Pronto para tentativa.' : `${track.milestone.remaining_exercises} exercício(s) restantes.` }}
                        </small>
                      </div>
                    </article>

                    <article
                      v-for="tip in roadmapTips"
                      :key="`${tip.title}-${tip.y}`"
                      class="track-map-tip"
                      :class="`track-map-tip--${tip.status}`"
                      :style="tipStyle(tip)"
                    >
                      <p class="eyebrow">Tip de estudo</p>
                      <strong>{{ tip.title }}</strong>
                      <p>{{ tip.copy }}</p>
                    </article>
                  </div>
                </div>
              </div>
            </div>

            <Drawer v-if="selectedExercise" v-model:open="drawerOpen" direction="right" :should-scale-background="false">
              <DrawerContent class="track-module-drawer">
                <DrawerHeader class="track-module-drawer-header">
                  <div>
                    <p class="eyebrow">Módulo selecionado</p>
                    <DrawerTitle class="track-module-drawer-title">{{ selectedExercise.title }}</DrawerTitle>
                    <DrawerDescription class="track-module-drawer-copy">{{ selectedExercise.concept_summary }}</DrawerDescription>
                  </div>
                  <button class="track-module-drawer-close" type="button" @click="closeExercisePanel" aria-label="Fechar módulo">
                    ×
                  </button>
                </DrawerHeader>

                <div class="track-module-drawer-meta">
                  <span class="track-status-badge" :class="`track-status-badge--${selectedExercise.progress.status}`">
                    {{ statusLabel(selectedExercise.progress.status) }}
                  </span>
                  <span class="track-module-chip">{{ selectedExercise.exercise_type_label }}</span>
                  <span class="track-module-chip">{{ selectedExercise.estimated_time_minutes }} min</span>
                </div>

                <div class="track-module-choice-grid">
                  <Card class="track-module-choice-card">
                    <CardHeader>
                      <p class="eyebrow">Aprofundamento Didático</p>
                      <CardTitle>Ir para explanation</CardTitle>
                      <CardDescription>
                        Abra a leitura progressiva do módulo em uma página dedicada, estilo leitura focada.
                      </CardDescription>
                    </CardHeader>
                    <CardContent class="track-module-choice-body">
                      <div class="track-module-note">
                        <strong>Resumo do módulo</strong>
                        <p>{{ selectedExercise.concept_summary }}</p>
                      </div>
                      <div class="track-module-note">
                        <strong>Por que abrir a explanation</strong>
                        <p>{{ selectedExercise.pedagogical_brief }}</p>
                      </div>
                      <Button variant="outline" class="w-full" @click="openDidacticPanel">
                        <BookOpenText :size="16" />
                        Abrir explanation
                      </Button>
                    </CardContent>
                  </Card>

                  <Card class="track-module-choice-card track-module-choice-card--action">
                    <CardHeader>
                      <p class="eyebrow">Área prática</p>
                      <CardTitle>Iniciar exercício</CardTitle>
                      <CardDescription>
                        Entre na arena com o módulo selecionado e continue a trilha no fluxo correto.
                      </CardDescription>
                    </CardHeader>
                    <CardContent class="track-module-choice-body">
                      <div class="track-module-note">
                        <strong>Objetivo desta rodada</strong>
                        <p>{{ selectedExercise.concept_summary }}</p>
                      </div>
                      <div class="track-module-nav">
                        <Button variant="outline" class="w-full" :disabled="!previousExercise" @click="goToPreviousExercise">
                          <ArrowRight :size="16" class="track-arrow track-arrow--prev" />
                          Etapa anterior
                        </Button>
                        <Button variant="outline" class="w-full" :disabled="!nextExercise" @click="goToNextExercise">
                          <ArrowRight :size="16" />
                          Próxima etapa
                        </Button>
                      </div>
                      <Button class="w-full" @click="openArena(selectedExercise.slug)">
                        <Play :size="16" />
                        Iniciar exercício
                      </Button>
                    </CardContent>
                  </Card>
                </div>
              </DrawerContent>
            </Drawer>
          </section>
        </div>
      </div>
    </main>

    <ProfileModal v-if="showProfile" @close="showProfile = false" />
  </div>
</template>
