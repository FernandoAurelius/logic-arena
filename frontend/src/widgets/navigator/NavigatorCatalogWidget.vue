<script setup lang="ts">
import { ArrowRight, Map, Play, Sparkles, Target } from 'lucide-vue-next'

import type { ModuleSummary, TrackSummary } from '@/entities/catalog'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/shared/ui/card'
import { ScrollArea } from '@/shared/ui/scroll-area'

defineProps<{
  modules: ModuleSummary[]
  visibleModules: ModuleSummary[]
  visibleTrackCount: number
  recommendedTrack: TrackSummary | null
  recommendedModule: ModuleSummary | null
  loading: boolean
  errorMessage: string
  activeModule: string
  activeStatus: 'all' | 'available' | 'in_progress' | 'passed'
  progressLabel: (track: TrackSummary) => string
  statusTone: (track: TrackSummary) => 'available' | 'in_progress' | 'passed'
}>()

const emit = defineEmits<{
  (event: 'update:activeModule', value: string): void
  (event: 'update:activeStatus', value: 'all' | 'available' | 'in_progress' | 'passed'): void
  (event: 'openTrack', slug: string): void
  (event: 'openTrackInArena', track: TrackSummary): void
  (event: 'openArena'): void
}>()
</script>

<template>
  <main class="navigator-workspace">
    <aside class="navigator-sidebar">
      <Card class="navigator-sidebar-card">
        <CardHeader>
          <p class="eyebrow">Controle</p>
          <CardTitle>Navegador</CardTitle>
          <CardDescription>Escolha a trilha certa antes de entrar na arena.</CardDescription>
        </CardHeader>
        <CardContent class="navigator-filter-stack">
          <div class="navigator-filter-group">
            <p class="section-label">Status</p>
            <div class="navigator-status-filter-row">
              <button class="navigator-filter-chip" :class="{ active: activeStatus === 'all' }" type="button" @click="emit('update:activeStatus', 'all')">Todos</button>
              <button class="navigator-filter-chip" :class="{ active: activeStatus === 'available' }" type="button" @click="emit('update:activeStatus', 'available')">Não iniciado</button>
              <button class="navigator-filter-chip" :class="{ active: activeStatus === 'in_progress' }" type="button" @click="emit('update:activeStatus', 'in_progress')">Em progresso</button>
              <button class="navigator-filter-chip" :class="{ active: activeStatus === 'passed' }" type="button" @click="emit('update:activeStatus', 'passed')">Masterizado</button>
            </div>
          </div>
          <button class="navigator-filter-button" :class="{ active: activeModule === 'all' }" type="button" @click="emit('update:activeModule', 'all')">
            Todos os módulos
          </button>
          <button
            v-for="module in modules"
            :key="module.slug"
            class="navigator-filter-button"
            :class="{ active: activeModule === module.slug }"
            type="button"
            @click="emit('update:activeModule', module.slug)"
          >
            {{ module.name }}
          </button>
        </CardContent>
      </Card>
    </aside>

    <section class="navigator-main">
      <div class="navigator-surface-header">
        <div class="navigator-surface-header__meta">
          <p class="eyebrow">Catálogo autenticado por módulos</p>
          <strong>{{ visibleModules.length }} módulos · {{ visibleTrackCount }} trilhas</strong>
        </div>
        <div class="navigator-hero-actions">
          <Button v-if="recommendedTrack" @click="emit('openTrack', recommendedTrack.slug)">
            <Target :size="16" />
            {{ recommendedModule ? `Seguir em ${recommendedModule.name}` : 'Abrir trilha atual' }}
          </Button>
          <Button variant="outline" @click="emit('openArena')">
            <ArrowRight :size="16" />
            Ir para a arena
          </Button>
        </div>
      </div>

      <ScrollArea class="navigator-main-scroll" viewport-class="navigator-main-viewport">
        <p v-if="errorMessage" class="notice error">{{ errorMessage }}</p>
        <div v-else-if="loading" class="navigator-empty-state">
          <Sparkles :size="18" />
          <span>Sincronizando catálogo autenticado...</span>
        </div>

        <div v-else class="navigator-category-stack">
          <section v-for="module in visibleModules" :key="module.slug" class="navigator-category-section">
            <div class="navigator-section-heading">
              <div>
                <p class="eyebrow">{{ module.name }}</p>
                <h2>{{ module.description || 'Trilhas organizadas por módulo didático.' }}</h2>
                <small>{{ module.audience }}</small>
              </div>
              <Badge variant="outline">{{ module.tracks.length }} trilhas</Badge>
            </div>

            <div class="navigator-track-grid">
              <Card
                v-for="track in module.tracks"
                :key="track.slug"
                class="navigator-track-card"
                :data-status="statusTone(track)"
              >
                <CardHeader>
                  <div class="navigator-card-topline">
                    <Badge variant="outline">{{ track.level_label }}</Badge>
                    <Badge variant="outline" :class="`navigator-status-badge navigator-status-badge--${statusTone(track)}`">
                      {{ progressLabel(track) }}
                    </Badge>
                  </div>
                  <CardTitle>{{ track.name }}</CardTitle>
                  <CardDescription>{{ track.goal }}</CardDescription>
                </CardHeader>
                <CardContent class="navigator-track-body">
                  <p class="navigator-track-description">{{ track.description }}</p>
                  <div class="navigator-track-stats">
                    <div class="navigator-stat-row navigator-stat-row--compact">
                      <small class="eyebrow">Progresso</small>
                      <strong>{{ track.progress_percent }}%</strong>
                    </div>
                    <div class="navigator-stat-row navigator-stat-row--compact">
                      <small class="eyebrow">Módulos</small>
                      <strong>{{ track.completed_exercises }}/{{ track.total_exercises }}</strong>
                    </div>
                    <div class="navigator-stat-row navigator-stat-row--stack">
                      <small class="eyebrow">Alvo</small>
                      <strong>{{ track.current_target_title ?? 'Masterizado' }}</strong>
                    </div>
                  </div>
                  <div class="navigator-progress-rail">
                    <div class="navigator-progress-rail-fill" :style="{ width: `${track.progress_percent}%` }"></div>
                  </div>
                  <div class="navigator-track-actions">
                    <Button class="w-full whitespace-normal text-center leading-tight" @click="emit('openTrack', track.slug)">
                      <Map :size="16" />
                      Mapa
                    </Button>
                    <Button
                      variant="outline"
                      class="w-full whitespace-normal text-center leading-tight"
                      :disabled="!track.current_target_slug"
                      @click="emit('openTrackInArena', track)"
                    >
                      <Play :size="16" />
                      Abrir
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </div>
          </section>
        </div>
      </ScrollArea>
    </section>
  </main>
</template>
