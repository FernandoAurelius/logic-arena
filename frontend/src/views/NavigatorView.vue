<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowRight, LogOut, Map, Play, Sparkles, Target, UserRound } from 'lucide-vue-next'
import type { infer as ZodInfer } from 'zod'

import { catalogApi } from '@/entities/catalog/api/catalog.api'
import { schemas } from '@/shared/api/generated'
import { useSession } from '@/entities/session'
import ProfileModal from '@/components/theme/ProfileModal.vue'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { ScrollArea } from '@/components/ui/scroll-area'

type NavigatorResponse = ZodInfer<typeof schemas.NavigatorResponseSchema>
type TrackSummary = ZodInfer<typeof schemas.TrackSummarySchema>
type ModuleSummary = ZodInfer<typeof schemas.NavigatorModuleSchema>

const router = useRouter()
const session = useSession()

const navigatorData = ref<NavigatorResponse | null>(null)
const loading = ref(false)
const errorMessage = ref('')
const activeModule = ref<string>('all')
const activeStatus = ref<'all' | 'available' | 'in_progress' | 'passed'>('all')
const showProfile = ref(false)

const modules = computed(() => navigatorData.value?.modules ?? [])
function matchesStatus(track: TrackSummary) {
  if (activeStatus.value === 'all') return true
  return statusTone(track) === activeStatus.value
}
const visibleModules = computed(() => {
  const selectedModules = activeModule.value === 'all'
    ? modules.value
    : modules.value.filter((module) => module.slug === activeModule.value)

  return selectedModules
    .map((module) => ({
      ...module,
      tracks: module.tracks.filter(matchesStatus),
    }))
    .filter((module) => module.tracks.length > 0)
})
const visibleTrackCount = computed(() => visibleModules.value.reduce((total, module) => total + module.tracks.length, 0))
const recommendedTrack = computed(() => {
  const slug = navigatorData.value?.recommended_track_slug
  if (!slug) return null
  for (const module of modules.value) {
    const track = module.tracks.find((candidate) => candidate.slug === slug)
    if (track) return track
  }
  return null
})
const recommendedModule = computed<ModuleSummary | null>(() => {
  const slug = navigatorData.value?.recommended_module_slug
  if (!slug) return null
  return modules.value.find((module) => module.slug === slug) ?? null
})

function progressLabel(track: TrackSummary) {
  if (track.progress_percent >= 100) return 'Masterizado'
  if (track.progress_percent > 0) return 'Em progresso'
  return 'Não iniciado'
}

function statusTone(track: TrackSummary) {
  if (track.progress_percent >= 100) return 'passed'
  if (track.progress_percent > 0) return 'in_progress'
  return 'available'
}

function openTrack(trackSlug: string) {
  void router.push({ name: 'track', params: { trackSlug } })
}

function openTrackInArena(track: TrackSummary) {
  void router.push({
    name: 'arena',
    query: {
      track: track.slug,
      exercise: track.current_target_slug ?? undefined,
    },
  })
}

async function loadNavigator() {
  loading.value = true
  errorMessage.value = ''

  try {
    navigatorData.value = await catalogApi.getNavigator(session.authHeader() ?? undefined)
  } catch (error) {
    console.error(error)
    errorMessage.value = 'Não foi possível carregar o Navegador agora.'
  } finally {
    loading.value = false
  }
}

async function logout() {
  session.clearSession()
  await router.push({ name: 'landing' })
}

onMounted(() => {
  void loadNavigator()
})
</script>

<template>
  <div class="navigator-page">
    <header class="topbar">
      <div class="topbar-left topbar-left--nav">
        <span class="brand-wordmark">LOGIC ARENA</span>
        <nav class="workspace-nav">
          <button class="workspace-nav-link workspace-nav-link--active" type="button">Navegador</button>
          <button class="workspace-nav-link" type="button" @click="router.push({ name: 'arena' })">Arena</button>
          <button class="workspace-nav-link" type="button" @click="router.push({ name: 'tutorial' })">Documentação</button>
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
                <button
                  class="navigator-filter-chip"
                  :class="{ active: activeStatus === 'all' }"
                  type="button"
                  @click="activeStatus = 'all'"
                >
                  Todos
                </button>
                <button
                  class="navigator-filter-chip"
                  :class="{ active: activeStatus === 'available' }"
                  type="button"
                  @click="activeStatus = 'available'"
                >
                  Não iniciado
                </button>
                <button
                  class="navigator-filter-chip"
                  :class="{ active: activeStatus === 'in_progress' }"
                  type="button"
                  @click="activeStatus = 'in_progress'"
                >
                  Em progresso
                </button>
                <button
                  class="navigator-filter-chip"
                  :class="{ active: activeStatus === 'passed' }"
                  type="button"
                  @click="activeStatus = 'passed'"
                >
                  Masterizado
                </button>
              </div>
            </div>
            <button
              class="navigator-filter-button"
                  :class="{ active: activeModule === 'all' }"
                  type="button"
                  @click="activeModule = 'all'"
                >
                  Todos os módulos
                </button>
                <button
              v-for="module in modules"
              :key="module.slug"
              class="navigator-filter-button"
              :class="{ active: activeModule === module.slug }"
              type="button"
              @click="activeModule = module.slug"
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
            <Button v-if="recommendedTrack" @click="openTrack(recommendedTrack.slug)">
              <Target :size="16" />
              {{ recommendedModule ? `Seguir em ${recommendedModule.name}` : 'Abrir trilha atual' }}
            </Button>
            <Button variant="outline" @click="router.push({ name: 'arena' })">
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
                      <Button class="w-full whitespace-normal text-center leading-tight" @click="openTrack(track.slug)">
                        <Map :size="16" />
                        Mapa
                      </Button>
                      <Button
                        variant="outline"
                        class="w-full whitespace-normal text-center leading-tight"
                        :disabled="!track.current_target_slug"
                        @click="openTrackInArena(track)"
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
    <ProfileModal v-if="showProfile" @close="showProfile = false" />
  </div>
</template>
