<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowRight, LogOut, Sparkles, Target, UserRound } from 'lucide-vue-next'
import type { infer as ZodInfer } from 'zod'

import { catalogApi } from '@/lib/api/client'
import { schemas } from '@/lib/api/generated'
import { useSession } from '@/lib/session'
import ProfileModal from '@/components/theme/ProfileModal.vue'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { ScrollArea } from '@/components/ui/scroll-area'

type NavigatorResponse = ZodInfer<typeof schemas.NavigatorResponseSchema>
type TrackSummary = ZodInfer<typeof schemas.TrackSummarySchema>

const router = useRouter()
const session = useSession()

const navigatorData = ref<NavigatorResponse | null>(null)
const loading = ref(false)
const errorMessage = ref('')
const activeCategory = ref<string>('all')
const activeStatus = ref<'all' | 'available' | 'in_progress' | 'passed'>('all')
const showProfile = ref(false)

const categories = computed(() => navigatorData.value?.categories ?? [])
function matchesStatus(track: TrackSummary) {
  if (activeStatus.value === 'all') return true
  return statusTone(track) === activeStatus.value
}
const visibleCategories = computed(() => {
  const selectedCategories = activeCategory.value === 'all'
    ? categories.value
    : categories.value.filter((category) => category.slug === activeCategory.value)

  return selectedCategories
    .map((category) => ({
      ...category,
      tracks: category.tracks.filter(matchesStatus),
    }))
    .filter((category) => category.tracks.length > 0)
})
const visibleTrackCount = computed(() => visibleCategories.value.reduce((total, category) => total + category.tracks.length, 0))
const recommendedTrack = computed(() => {
  const slug = navigatorData.value?.recommended_track_slug
  if (!slug) return null
  for (const category of categories.value) {
    const track = category.tracks.find((candidate) => candidate.slug === slug)
    if (track) return track
  }
  return null
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
    navigatorData.value = await catalogApi.get('/api/catalog/navigator', {
      headers: { authorization: session.authHeader() ?? undefined },
    })
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
              :class="{ active: activeCategory === 'all' }"
              type="button"
              @click="activeCategory = 'all'"
            >
              Todas as categorias
            </button>
            <button
              v-for="category in categories"
              :key="category.slug"
              class="navigator-filter-button"
              :class="{ active: activeCategory === category.slug }"
              type="button"
              @click="activeCategory = category.slug"
            >
              {{ category.name }}
            </button>
          </CardContent>
        </Card>
      </aside>

      <section class="navigator-main">
        <div class="navigator-surface-header">
          <div class="navigator-surface-header__meta">
            <p class="eyebrow">Catálogo autenticado</p>
            <strong>{{ visibleCategories.length }} categorias · {{ visibleTrackCount }} trilhas</strong>
          </div>
          <div class="navigator-hero-actions">
            <Button v-if="recommendedTrack" @click="openTrack(recommendedTrack.slug)">
              <Target :size="16" />
              Abrir trilha atual
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
            <section v-for="category in visibleCategories" :key="category.slug" class="navigator-category-section">
              <div class="navigator-section-heading">
                <div>
                  <p class="eyebrow">{{ category.name }}</p>
                  <h2>{{ category.description || 'Trilhas organizadas por domínio de prática.' }}</h2>
                </div>
                <Badge variant="outline">{{ category.tracks.length }} trilhas</Badge>
              </div>

              <div class="navigator-track-grid">
                <Card
                  v-for="track in category.tracks"
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
                      <Button class="w-full" @click="openTrack(track.slug)">
                        <Target :size="16" />
                        Ver mapa
                      </Button>
                      <Button variant="outline" class="w-full" :disabled="!track.current_target_slug" @click="openTrackInArena(track)">
                        Abrir na arena
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
