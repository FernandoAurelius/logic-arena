import { computed, ref, watch, type Ref } from 'vue'

import type { TrackDetail, TrackExercise } from '@/entities/track'

type TrackNodeLayout = {
  exercise: TrackExercise
  side: 'left' | 'right'
  anchorX: number
  anchorY: number
  calloutX: number
  calloutY: number
}

type TrackTipLayout = {
  id: string
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

type Rect = {
  x: number
  y: number
  width: number
  height: number
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
const ROADMAP_CURVE_OFFSETS = [-148, 122, -102, 152, -124, 104, -86, 132]

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

export function useTrackRoadmap(track: Ref<TrackDetail>) {
  const selectedExerciseSlug = ref('')
  const drawerOpen = ref(false)

  const orderedExercises = computed(() => track.value.exercises ?? [])
  const selectedExercise = computed<TrackExercise | null>(
    () => orderedExercises.value.find((exercise) => exercise.slug === selectedExerciseSlug.value) ?? orderedExercises.value[0] ?? null,
  )
  const selectedExerciseIndex = computed(() =>
    selectedExercise.value ? orderedExercises.value.findIndex((exercise) => exercise.slug === selectedExercise.value?.slug) : -1,
  )
  const previousExercise = computed(() => (selectedExerciseIndex.value > 0 ? orderedExercises.value[selectedExerciseIndex.value - 1] ?? null : null))
  const nextExercise = computed(() =>
    selectedExerciseIndex.value >= 0 ? orderedExercises.value[selectedExerciseIndex.value + 1] ?? null : null,
  )

  watch(
    () => [track.value.slug, track.value.current_target_slug, track.value.exercises[0]?.slug] as const,
    () => {
      selectedExerciseSlug.value = track.value.current_target_slug ?? track.value.exercises[0]?.slug ?? ''
      drawerOpen.value = false
    },
    { immediate: true },
  )

  const trackNodeLayouts = computed<TrackNodeLayout[]>(() =>
    orderedExercises.value.map((exercise, index) => {
      const side = index % 2 === 0 ? 'left' : 'right'
      const anchorY = MAP_TOP_PADDING + index * MAP_ROW_GAP
      const anchorX = MAP_WIDTH / 2 + ROADMAP_CURVE_OFFSETS[index % ROADMAP_CURVE_OFFSETS.length]
      const calloutXBase = side === 'left' ? anchorX - MAP_CALLOUT_WIDTH - 72 : anchorX + 72
      const calloutX = Math.max(30, Math.min(MAP_WIDTH - MAP_CALLOUT_WIDTH - 30, calloutXBase))

      return {
        exercise,
        side,
        anchorX,
        anchorY,
        calloutX,
        calloutY: anchorY - MAP_CALLOUT_HEIGHT / 2,
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
      ...track.value.concepts.map((concept) => ({
        title: concept.title,
        copy: concept.summary,
      })),
      ...track.value.prerequisites.map((item) => ({
        title: 'Fundamento-chave',
        copy: item,
      })),
    ].slice(0, 3)

    const placedTips: Rect[] = []

    return source.map((tip, index) => {
      const current = trackNodeLayouts.value[index]
      const tipId = `${current?.exercise.slug ?? track.value.slug}-tip-${index}`
      if (!current) {
        return {
          id: tipId,
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

      const candidate =
        preferredCandidates
          .map(clampRect)
          .find(
            (rect) =>
              !rectsOverlap(rect, calloutRect, 18) &&
              placedTips.every((placed) => !rectsOverlap(rect, placed, 18)),
          ) ?? clampRect(preferredCandidates[0]!)

      placedTips.push(candidate)

      return {
        id: tipId,
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

  function closeExercisePanel() {
    drawerOpen.value = false
  }

  function goToPreviousExercise() {
    if (!previousExercise.value) return
    openExercisePanel(previousExercise.value.slug)
  }

  function goToNextExercise() {
    if (!nextExercise.value) return
    openExercisePanel(nextExercise.value.slug)
  }

  return {
    MAP_WIDTH,
    orderedExercises,
    selectedExercise,
    previousExercise,
    nextExercise,
    selectedExerciseSlug,
    drawerOpen,
    trackNodeLayouts,
    roadmapUnits,
    roadmapTips,
    milestoneLayout,
    roadmapHeight,
    roadmapViewBox,
    roadmapPath,
    statusLabel,
    cardStyle,
    tipStyle,
    unitStyle,
    openExercisePanel,
    closeExercisePanel,
    goToPreviousExercise,
    goToNextExercise,
  }
}
