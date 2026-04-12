<script setup lang="ts">
import { toRef } from 'vue'
import { ArrowRight, BookOpenText, Play, ShieldCheck } from 'lucide-vue-next'

import type { TrackDetail } from '@/entities/track'
import { useTrackRoadmap } from '@/features/track/roadmap/model/useTrackRoadmap'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Drawer, DrawerContent, DrawerDescription, DrawerHeader, DrawerTitle } from '@/components/ui/drawer'

const props = defineProps<{
  track: TrackDetail
}>()

const emit = defineEmits<{
  (event: 'open-explanation', slug: string): void
  (event: 'open-arena', slug?: string): void
}>()

const trackRef = toRef(props, 'track')
const roadmap = useTrackRoadmap(trackRef)

function openDidacticPanel() {
  const targetSlug =
    roadmap.selectedExercise.value?.slug ??
    props.track.current_target_slug ??
    roadmap.orderedExercises.value[0]?.slug
  if (targetSlug) {
    emit('open-explanation', targetSlug)
  }
}

function openArena(slug?: string) {
  emit('open-arena', slug)
}
</script>

<template>
  <section class="track-roadmap-widget">
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
              <Button variant="outline" class="w-full" @click="openDidacticPanel">
                <BookOpenText :size="16" />
                Aprofundamento didático
              </Button>
            </CardContent>
          </Card>
        </aside>

        <div class="track-map-canvas">
          <div class="track-map-shell" :style="{ height: `${roadmap.roadmapHeight.value}px`, width: `${roadmap.MAP_WIDTH}px` }">
            <svg class="track-map-svg" :viewBox="roadmap.roadmapViewBox.value" preserveAspectRatio="xMidYMin slice" aria-hidden="true">
              <path class="track-map-path" :d="roadmap.roadmapPath.value" />
              <path
                v-for="tip in roadmap.roadmapTips.value"
                :key="`tip-path-${tip.id}`"
                class="track-map-tip-path"
                :d="tip.pathD"
              />
            </svg>

            <div
              v-for="unit in roadmap.roadmapUnits.value"
              :key="unit.label"
              class="track-map-unit"
              :style="roadmap.unitStyle(unit)"
            >
              {{ unit.label }}
            </div>

            <div
              v-for="(layout, index) in roadmap.trackNodeLayouts.value"
              :key="layout.exercise.slug"
              class="track-map-stop"
              :class="[
                `track-map-stop--${layout.exercise.progress.status}`,
                roadmap.selectedExerciseSlug.value === layout.exercise.slug && 'track-map-stop--selected',
                track.current_target_slug === layout.exercise.slug && 'track-map-stop--current',
              ]"
              :style="{ left: `${layout.anchorX}px`, top: `${layout.anchorY}px` }"
              aria-hidden="true"
            >
              <span class="track-map-stop-ring"></span>
              <span class="track-map-stop-core"></span>
              <span class="track-map-stop-label">{{ index + 1 }}</span>
            </div>

            <article
              v-for="layout in roadmap.trackNodeLayouts.value"
              :key="layout.exercise.slug"
              class="track-map-callout"
              :class="[
                `track-map-callout--${layout.exercise.progress.status}`,
                roadmap.selectedExerciseSlug.value === layout.exercise.slug && 'track-map-callout--selected',
                track.current_target_slug === layout.exercise.slug && 'track-map-callout--current',
              ]"
              :style="roadmap.cardStyle(layout)"
            >
              <button class="track-map-callout-hit" type="button" @click="roadmap.openExercisePanel(layout.exercise.slug)">
                <div class="track-map-callout-head">
                  <span class="track-status-badge" :class="`track-status-badge--${layout.exercise.progress.status}`">
                    {{ roadmap.statusLabel(layout.exercise.progress.status) }}
                  </span>
                  <small class="eyebrow">Step {{ layout.exercise.position }}</small>
                </div>
                <strong>{{ layout.exercise.title }}</strong>
                <p>{{ layout.exercise.concept_summary }}</p>
                <div class="track-map-callout-head">
                  <small class="eyebrow">{{ layout.exercise.exercise_type_label }}</small>
                  <small class="eyebrow">{{ layout.exercise.estimated_time_minutes }} min</small>
                </div>
              </button>
            </article>

            <article
              class="track-map-milestone-card track-milestone-card"
              :class="track.milestone.locked ? 'track-milestone-card--locked' : ''"
              :style="{
                left: `${roadmap.milestoneLayout.value.cardX}px`,
                top: `${roadmap.milestoneLayout.value.cardY}px`,
                width: `${roadmap.milestoneLayout.value.cardWidth}px`,
              }"
            >
              <div class="track-milestone-icon">
                <ShieldCheck :size="20" />
              </div>
              <div class="track-milestone-copy">
                <small class="eyebrow">Milestone checkpoint</small>
                <h3>{{ track.milestone.title }}</h3>
                <p>{{ track.milestone.summary }}</p>
                <small>
                  {{ track.milestone.locked ? `${track.milestone.remaining_exercises} exercício(s) restantes.` : 'Pronto para tentativa.' }}
                </small>
              </div>
            </article>

            <article
              v-for="tip in roadmap.roadmapTips.value"
              :key="tip.id"
              class="track-map-tip"
              :class="`track-map-tip--${tip.status}`"
              :style="roadmap.tipStyle(tip)"
            >
              <p class="eyebrow">Tip de estudo</p>
              <strong>{{ tip.title }}</strong>
              <p>{{ tip.copy }}</p>
            </article>
          </div>
        </div>
      </div>
    </div>

    <Drawer v-if="roadmap.selectedExercise.value" v-model:open="roadmap.drawerOpen.value" direction="right" :should-scale-background="false">
      <DrawerContent class="track-module-drawer">
        <DrawerHeader class="track-module-drawer-header">
          <div>
            <p class="eyebrow">Módulo selecionado</p>
            <DrawerTitle class="track-module-drawer-title">{{ roadmap.selectedExercise.value.title }}</DrawerTitle>
            <DrawerDescription class="track-module-drawer-copy">{{ roadmap.selectedExercise.value.concept_summary }}</DrawerDescription>
          </div>
          <button class="track-module-drawer-close" type="button" @click="roadmap.closeExercisePanel" aria-label="Fechar módulo">
            ×
          </button>
        </DrawerHeader>

        <div class="track-module-drawer-meta">
          <span class="track-status-badge" :class="`track-status-badge--${roadmap.selectedExercise.value.progress.status}`">
            {{ roadmap.statusLabel(roadmap.selectedExercise.value.progress.status) }}
          </span>
          <span class="track-module-chip">{{ roadmap.selectedExercise.value.exercise_type_label }}</span>
          <span class="track-module-chip">{{ roadmap.selectedExercise.value.estimated_time_minutes }} min</span>
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
                <p>{{ roadmap.selectedExercise.value.concept_summary }}</p>
              </div>
              <div class="track-module-note">
                <strong>Por que abrir a explanation</strong>
                <p>{{ roadmap.selectedExercise.value.pedagogical_brief }}</p>
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
                <p>{{ roadmap.selectedExercise.value.concept_summary }}</p>
              </div>
              <div class="track-module-nav">
                <Button variant="outline" class="w-full" :disabled="!roadmap.previousExercise.value" @click="roadmap.goToPreviousExercise">
                  <ArrowRight :size="16" class="track-arrow track-arrow--prev" />
                  Etapa anterior
                </Button>
                <Button variant="outline" class="w-full" :disabled="!roadmap.nextExercise.value" @click="roadmap.goToNextExercise">
                  <ArrowRight :size="16" />
                  Próxima etapa
                </Button>
              </div>
              <Button class="w-full" @click="openArena(roadmap.selectedExercise.value.slug)">
                <Play :size="16" />
                Iniciar exercício
              </Button>
            </CardContent>
          </Card>
        </div>
      </DrawerContent>
    </Drawer>
  </section>
</template>

<style>
.track-roadmap-widget {
  display: grid;
  gap: 1rem;
}

.track-roadmap-grid {
  display: grid;
}

.track-map-stage {
  --map-surface: color-mix(in srgb, var(--surface) 96%, transparent);
  --map-surface-elevated: color-mix(in srgb, var(--surface-container) 88%, transparent);
  --map-line: color-mix(in srgb, var(--outline) 62%, transparent);
  --map-card-border: var(--on-surface);
  --map-card-shadow: var(--on-surface);
  --map-text: var(--on-surface);
  --map-text-muted: var(--on-surface-variant);
  position: relative;
  min-height: min(88vh, 1120px);
  border: 2px solid var(--on-surface);
  box-shadow: 6px 6px 0 var(--on-surface);
  display: grid;
  grid-template-columns: minmax(19rem, 22rem) minmax(0, 1fr);
  align-items: start;
  gap: 1.35rem;
  padding: 1.25rem;
  background:
    linear-gradient(color-mix(in srgb, var(--outline) 8%, transparent) 1px, transparent 1px),
    linear-gradient(90deg, color-mix(in srgb, var(--outline) 8%, transparent) 1px, transparent 1px),
    color-mix(in srgb, var(--surface) 96%, transparent);
  background-size: 1.9rem 1.9rem;
  overflow: hidden;
}

.track-map-stage::after {
  content: '';
  position: absolute;
  inset: auto 1.25rem 1.25rem auto;
  width: 260px;
  height: 1px;
  background: linear-gradient(90deg, transparent, color-mix(in srgb, var(--outline) 80%, transparent));
  pointer-events: none;
}

.track-map-foundations {
  display: grid;
  align-content: start;
  gap: 1rem;
  position: sticky;
  top: 0;
}

.track-map-foundations-title {
  display: grid;
  gap: 0.15rem;
}

.track-map-foundations-title h2 {
  margin: 0;
  font-family: 'Space Grotesk', sans-serif;
  font-size: 2rem;
  line-height: 0.92;
  text-transform: uppercase;
  letter-spacing: -0.05em;
}

.track-summary-card {
  border: 2px solid var(--on-surface);
  box-shadow: 6px 6px 0 var(--on-surface);
  background: color-mix(in srgb, var(--surface) 94%, transparent);
  align-self: start;
}

.track-summary-card .card-header,
.track-summary-card .card-content,
.track-summary-body,
.track-module-choice-body,
.track-module-note,
.track-module-nav {
  display: grid;
  gap: 0.9rem;
}

.track-summary-card .card-title {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 1.2rem;
  line-height: 1.05;
  letter-spacing: -0.03em;
}

.track-summary-card .card-description,
.track-summary-copy,
.track-module-note p,
.track-module-drawer-copy {
  color: var(--on-surface-variant);
  line-height: 1.45;
}

.track-summary-progress {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 3rem;
  line-height: 1;
}

.track-summary-stats {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1rem;
}

.track-summary-stats > div {
  display: grid;
  gap: 0.22rem;
  min-width: 0;
}

.track-summary-stats strong {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 1rem;
  line-height: 1.3;
  overflow-wrap: anywhere;
}

.track-map-canvas {
  min-width: 0;
  min-height: 0;
  height: min(88vh, 1120px);
  overflow: auto;
  overscroll-behavior: contain;
  scrollbar-gutter: stable both-edges;
  padding: 0 0 0 2rem;
}

.track-map-shell {
  position: relative;
  margin: 0 auto;
}

.track-map-svg {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  overflow: visible;
  pointer-events: none;
}

.track-map-path {
  fill: none;
  stroke: color-mix(in srgb, var(--primary) 20%, var(--map-line));
  stroke-width: 4;
  stroke-linecap: round;
  stroke-dasharray: 4 16;
}

.track-map-unit {
  position: absolute;
  z-index: 2;
  padding: 0.3rem 0.72rem;
  border: 1px dashed color-mix(in srgb, var(--primary) 34%, var(--map-line));
  background: color-mix(in srgb, var(--map-surface-elevated) 92%, transparent);
  font-family: 'Space Grotesk', sans-serif;
  font-size: 0.74rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--primary);
}

.track-map-stop {
  position: absolute;
  z-index: 3;
  width: 72px;
  height: 72px;
  transform: translate(-50%, -50%);
  display: grid;
  place-items: center;
}

.track-map-stop-ring,
.track-map-stop-core {
  position: absolute;
  border-radius: 999px;
}

.track-map-stop-ring {
  width: 72px;
  height: 72px;
  border: 2px solid color-mix(in srgb, var(--map-line) 85%, transparent);
  background: color-mix(in srgb, var(--map-surface) 80%, transparent);
}

.track-map-stop-core {
  width: 52px;
  height: 52px;
  border: 2px solid color-mix(in srgb, var(--map-card-border) 75%, transparent);
  background: color-mix(in srgb, var(--map-surface-elevated) 92%, transparent);
}

.track-map-stop-label {
  position: relative;
  z-index: 1;
  font-family: 'Space Grotesk', sans-serif;
  font-size: 1.4rem;
  font-weight: 700;
  color: color-mix(in srgb, var(--map-text) 82%, transparent);
}

.track-map-stop--passed .track-map-stop-core {
  background: color-mix(in srgb, #2f9e44 88%, transparent);
  border-color: color-mix(in srgb, #2f9e44 76%, var(--map-card-border));
}

.track-map-stop--passed .track-map-stop-label {
  color: #f6fffa;
}

.track-map-stop--in_progress .track-map-stop-core {
  background: color-mix(in srgb, #f3c261 88%, transparent);
  border-color: color-mix(in srgb, #e3a730 90%, var(--map-card-border));
}

.track-map-stop--available .track-map-stop-core {
  background: color-mix(in srgb, var(--surface) 96%, transparent);
  border-color: color-mix(in srgb, var(--primary) 74%, transparent);
}

.track-map-stop--available .track-map-stop-ring {
  border-color: color-mix(in srgb, var(--primary) 46%, var(--map-line));
}

.track-map-stop--locked {
  opacity: 0.7;
}

.track-map-stop--current .track-map-stop-ring {
  animation: track-node-pulse 1.9s ease-in-out infinite;
  border-color: color-mix(in srgb, var(--primary) 65%, #fff);
}

.track-map-stop--current .track-map-stop-core {
  box-shadow: 0 0 0 8px color-mix(in srgb, var(--primary) 18%, transparent);
}

.track-map-stop--selected {
  transform: translate(-50%, -50%) scale(1.06);
}

.track-map-callout {
  position: absolute;
  z-index: 2;
}

.track-map-callout-hit {
  width: 100%;
  display: grid;
  gap: 0.65rem;
  border: 2px solid color-mix(in srgb, var(--map-card-border) 52%, transparent);
  background: color-mix(in srgb, var(--map-surface-elevated) 94%, transparent);
  box-shadow: 4px 4px 0 color-mix(in srgb, var(--map-card-shadow) 62%, transparent);
  padding: 0.8rem 0.9rem;
  color: var(--map-text);
  text-align: left;
  cursor: pointer;
  transition: transform 150ms ease, box-shadow 150ms ease, border-color 150ms ease;
}

.track-map-callout-head {
  display: flex;
  justify-content: space-between;
  gap: 0.75rem;
  align-items: start;
}

.track-map-callout strong {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 1.05rem;
  line-height: 1.05;
  text-transform: uppercase;
  letter-spacing: -0.03em;
  color: var(--map-text);
}

.track-map-callout p {
  margin: 0;
  color: var(--map-text-muted);
  line-height: 1.45;
}

.track-map-callout--available .track-map-callout-hit {
  border-color: color-mix(in srgb, var(--primary) 52%, var(--map-card-border));
}

.track-map-callout--in_progress .track-map-callout-hit {
  border-color: color-mix(in srgb, #f3c261 68%, var(--map-card-border));
  box-shadow: 5px 5px 0 color-mix(in srgb, #f3c261 25%, transparent);
}

.track-map-callout--passed .track-map-callout-hit {
  border-color: color-mix(in srgb, #2f9e44 54%, var(--map-card-border));
  box-shadow: 5px 5px 0 color-mix(in srgb, #2f9e44 22%, transparent);
}

.track-map-callout--locked {
  opacity: 0.64;
}

.track-map-callout--selected .track-map-callout-hit {
  border-color: #3f7cff;
  box-shadow: 7px 7px 0 color-mix(in srgb, #3f7cff 28%, transparent);
}

.track-map-callout--current .track-map-callout-hit {
  border-width: 3px;
}

.track-map-callout-hit:hover {
  transform: translate(-2px, -2px);
  box-shadow: 7px 7px 0 color-mix(in srgb, var(--primary) 20%, var(--map-card-shadow));
}

.track-status-badge {
  display: inline-flex;
  align-items: center;
  padding: 0.28rem 0.6rem;
  border: 2px solid currentColor;
  font-family: 'Space Grotesk', sans-serif;
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  background: color-mix(in srgb, var(--map-surface-elevated) 94%, transparent);
}

.track-status-badge--passed {
  color: #206c34;
  background: color-mix(in srgb, #2f9e44 12%, var(--map-surface-elevated));
}

.track-status-badge--in_progress {
  color: #8a5a06;
  background: color-mix(in srgb, #f3c261 18%, var(--map-surface-elevated));
}

.track-status-badge--available {
  color: var(--primary);
  background: color-mix(in srgb, var(--primary) 10%, var(--map-surface-elevated));
}

.track-status-badge--locked {
  color: var(--map-text-muted);
  background: color-mix(in srgb, var(--map-surface) 65%, var(--map-surface-elevated));
}

.track-map-tip {
  position: absolute;
  z-index: 1;
  width: 220px;
  min-height: 112px;
  display: grid;
  align-content: start;
  gap: 0.4rem;
  padding: 0.8rem 0.9rem;
  border: 1px dashed color-mix(in srgb, var(--primary) 46%, var(--map-card-border));
  background: color-mix(in srgb, var(--map-surface-elevated) 94%, transparent);
  box-shadow: 4px 4px 0 color-mix(in srgb, var(--map-card-shadow) 70%, transparent);
}

.track-map-tip-path {
  fill: none;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-dasharray: 3 9;
  stroke-width: 2;
  stroke: color-mix(in srgb, var(--primary) 34%, var(--map-line));
}

.track-map-tip--locked {
  color: color-mix(in srgb, var(--map-text-muted) 88%, transparent);
  background: color-mix(in srgb, var(--map-surface) 74%, var(--map-surface-elevated));
  border-color: color-mix(in srgb, var(--outline) 56%, transparent);
  box-shadow: 4px 4px 0 color-mix(in srgb, var(--outline) 28%, transparent);
  opacity: 0.72;
  filter: saturate(0.25) blur(0.35px);
}

.track-map-tip--locked strong,
.track-map-tip--locked p,
.track-map-tip--locked .eyebrow {
  color: color-mix(in srgb, var(--map-text-muted) 92%, transparent);
}

.track-map-tip strong {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 0.92rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--map-text);
}

.track-map-tip p {
  margin: 0;
  color: var(--map-text-muted);
  line-height: 1.45;
  font-size: 0.82rem;
}

.track-map-milestone-card {
  position: absolute;
}

.track-milestone-card {
  position: relative;
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 1rem;
  background: color-mix(in srgb, var(--primary) 14%, var(--map-surface-elevated));
  color: var(--map-text);
  border: 2px solid var(--on-surface);
  box-shadow: 8px 8px 0 color-mix(in srgb, var(--primary) 55%, var(--on-surface));
  padding: 1.1rem 1.2rem;
}

.track-milestone-card p,
.track-milestone-card small {
  color: var(--map-text-muted);
}

.track-milestone-card--locked {
  background: color-mix(in srgb, var(--surface-container) 88%, transparent);
  color: var(--on-surface);
  box-shadow: 6px 6px 0 var(--outline);
}

.track-milestone-card--locked p,
.track-milestone-card--locked small {
  color: var(--on-surface-variant);
}

.track-milestone-copy {
  display: grid;
  gap: 0.35rem;
}

.track-milestone-copy h3 {
  margin: 0;
  font-family: 'Space Grotesk', sans-serif;
  font-size: 1.55rem;
  line-height: 1;
  text-transform: uppercase;
  letter-spacing: -0.04em;
}

.track-milestone-copy p {
  margin: 0;
  line-height: 1.55;
}

.track-milestone-icon {
  width: 2.8rem;
  height: 2.8rem;
  display: grid;
  place-items: center;
  border: 2px solid currentColor;
}

.track-module-drawer[data-slot='drawer-content'] {
  width: min(42rem, 100vw) !important;
  max-width: 42rem !important;
  height: 100vh;
  overflow: auto;
  padding: 1.2rem;
  border-left: 2px solid var(--on-surface);
  border-radius: 0;
  background: color-mix(in srgb, var(--surface) 97%, transparent);
  box-shadow: -10px 0 26px color-mix(in srgb, var(--map-card-shadow) 55%, transparent);
  display: grid;
  align-content: start;
  gap: 1rem;
}

[data-slot='drawer-overlay'] {
  background: color-mix(in srgb, var(--modal-overlay) 86%, transparent);
  backdrop-filter: blur(4px);
}

.track-module-drawer-header {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: start;
  padding: 0;
}

.track-module-drawer-title {
  margin: 0.2rem 0 0;
  font-family: 'Space Grotesk', sans-serif;
  font-size: 2rem;
  line-height: 0.95;
  letter-spacing: -0.04em;
  text-transform: uppercase;
}

.track-module-drawer-close {
  width: 2.5rem;
  height: 2.5rem;
  display: grid;
  place-items: center;
  border: 2px solid var(--on-surface);
  background: var(--surface);
  color: var(--on-surface);
  font-size: 1.35rem;
  cursor: pointer;
}

.track-module-drawer-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.7rem;
}

.track-module-chip {
  display: inline-flex;
  align-items: center;
  padding: 0.32rem 0.7rem;
  border: 1px solid var(--outline);
  background: var(--surface-container);
  color: var(--on-surface-variant);
  font-family: 'Space Grotesk', sans-serif;
  font-size: 0.74rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.track-module-choice-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1rem;
  align-items: start;
}

.track-module-choice-card {
  min-width: 0;
  border: 2px solid var(--on-surface);
  box-shadow: 6px 6px 0 var(--on-surface);
  background: color-mix(in srgb, var(--surface) 96%, transparent);
}

.track-module-choice-card--action {
  background: color-mix(in srgb, var(--primary) 8%, var(--surface));
}

.track-module-note {
  padding: 0.85rem 0.9rem;
  border: 1px dashed var(--outline);
  background: color-mix(in srgb, var(--surface-container) 72%, transparent);
}

.track-module-note strong {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 0.78rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.track-module-choice-card .inline-flex {
  width: 100%;
  justify-content: center;
}

.track-arrow--prev {
  transform: rotate(180deg);
}

@media (max-width: 1280px) {
  .track-map-stage {
    grid-template-columns: 1fr;
  }

  .track-map-foundations {
    position: relative;
    top: auto;
    left: auto;
    width: min(100%, 24rem);
  }

  .track-map-shell {
    width: 1080px;
    margin: 0;
  }

  .track-map-canvas {
    padding-left: 0;
  }
}

@media (max-width: 900px) {
  .track-map-stage {
    padding: 0.85rem;
  }

  .track-map-shell {
    width: 940px;
  }

  .track-module-drawer[data-slot='drawer-content'] {
    width: 100% !important;
    max-width: 100% !important;
    border-left: none;
    border-top: 2px solid var(--on-surface);
  }

  .track-module-choice-grid,
  .track-summary-stats {
    grid-template-columns: 1fr;
  }
}
</style>
