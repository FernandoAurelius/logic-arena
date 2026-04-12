<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowRight, Compass, LogOut, Route, Sparkles, Target, UserRound } from 'lucide-vue-next'
import type { infer as ZodInfer } from 'zod'

import { catalogApi } from '@/lib/api/client'
import { schemas } from '@/lib/api/generated'
import { useSession } from '@/lib/session'
import ProfileModal from '@/components/theme/ProfileModal.vue'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

type NavigatorResponse = ZodInfer<typeof schemas.NavigatorResponseSchema>
type TrackSummary = ZodInfer<typeof schemas.TrackSummarySchema>

const router = useRouter()
const session = useSession()

const navigatorData = ref<NavigatorResponse | null>(null)
const loading = ref(false)
const errorMessage = ref('')
const activeCategory = ref<string>('all')
const showProfile = ref(false)

const categories = computed(() => navigatorData.value?.categories ?? [])
const visibleCategories = computed(() => {
  if (activeCategory.value === 'all') return categories.value
  return categories.value.filter((category) => category.slug === activeCategory.value)
})
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
    errorMessage.value = 'Não foi possível carregar o Navigator agora.'
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
          <button class="workspace-nav-link workspace-nav-link--active" type="button">Navigator</button>
          <button class="workspace-nav-link" type="button" @click="router.push({ name: 'arena' })">Arena</button>
          <button class="workspace-nav-link" type="button" @click="router.push({ name: 'tutorial' })">Documentation</button>
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
            <strong>LEVEL {{ session.currentUser.value?.level ?? 1 }}</strong>
            <span>{{ session.currentUser.value?.nickname ?? 'operator' }}</span>
            <small>{{ session.currentUser.value?.xp_total ?? 0 }} XP totais</small>
          </div>
        </div>
      </div>
    </header>

    <main class="navigator-workspace">
      <aside class="navigator-sidebar">
        <Card class="navigator-sidebar-card">
          <CardHeader>
            <p class="eyebrow">Control Stack</p>
            <CardTitle>Navigator</CardTitle>
            <CardDescription>Escolha a trilha certa antes de entrar na arena.</CardDescription>
          </CardHeader>
          <CardContent class="navigator-filter-stack">
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

        <Card class="navigator-sidebar-card">
          <CardHeader>
            <p class="eyebrow">Recommended Path</p>
            <CardTitle>{{ recommendedTrack?.name ?? 'Sem recomendação ainda' }}</CardTitle>
            <CardDescription>
              {{ recommendedTrack?.goal ?? 'Quando o catálogo carregar, o próximo passo recomendado aparece aqui.' }}
            </CardDescription>
          </CardHeader>
          <CardContent class="navigator-recommendation-body">
            <div class="navigator-kpi-row">
              <div>
                <small class="eyebrow">Progresso</small>
                <strong>{{ recommendedTrack?.progress_percent ?? 0 }}%</strong>
              </div>
              <div>
                <small class="eyebrow">Target</small>
                <strong>{{ recommendedTrack?.current_target_title ?? 'A definir' }}</strong>
              </div>
            </div>
            <div class="navigator-hero-actions">
              <Button v-if="recommendedTrack" class="w-full" @click="openTrack(recommendedTrack.slug)">
                Ver Mapa
                <ArrowRight :size="16" />
              </Button>
              <Button v-if="recommendedTrack" variant="outline" class="w-full" @click="openTrackInArena(recommendedTrack)">
                Abrir Na Arena
              </Button>
            </div>
          </CardContent>
        </Card>
      </aside>

      <section class="navigator-main">
        <div class="navigator-hero">
          <div>
            <p class="eyebrow">Architectural Registry</p>
            <h1 class="navigator-title">Navigator</h1>
            <p class="navigator-copy">
              Navegue por categorias e trilhas reais do catálogo. Aqui o foco é escolher o próximo bloco de prática com contexto,
              não apenas abrir qualquer exercício.
            </p>
          </div>
          <div class="navigator-hero-actions">
            <Button v-if="recommendedTrack" @click="openTrack(recommendedTrack.slug)">
              <Route :size="16" />
              Abrir Trilha Atual
            </Button>
            <Button variant="outline" @click="router.push({ name: 'arena' })">
              <Compass :size="16" />
              Ir Para Arena
            </Button>
          </div>
        </div>

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
              <Card v-for="track in category.tracks" :key="track.slug" class="navigator-track-card">
                <CardHeader>
                  <div class="navigator-card-topline">
                    <Badge variant="outline">{{ track.level_label }}</Badge>
                    <Badge variant="outline">{{ progressLabel(track) }}</Badge>
                  </div>
                  <CardTitle>{{ track.name }}</CardTitle>
                  <CardDescription>{{ track.goal }}</CardDescription>
                </CardHeader>
                <CardContent class="navigator-track-body">
                  <p class="navigator-track-description">{{ track.description }}</p>
                  <div class="navigator-track-stats">
                    <div>
                      <small class="eyebrow">Progresso</small>
                      <strong>{{ track.progress_percent }}%</strong>
                    </div>
                    <div>
                      <small class="eyebrow">Módulos</small>
                      <strong>{{ track.completed_exercises }}/{{ track.total_exercises }}</strong>
                    </div>
                    <div>
                      <small class="eyebrow">Target</small>
                      <strong>{{ track.current_target_title ?? 'Masterizado' }}</strong>
                    </div>
                  </div>
                  <div class="navigator-progress-rail">
                    <div class="navigator-progress-rail-fill" :style="{ width: `${track.progress_percent}%` }"></div>
                  </div>
                  <div class="navigator-track-actions">
                    <Button class="w-full" @click="openTrack(track.slug)">
                      <Target :size="16" />
                      Ver Mapa
                    </Button>
                    <Button variant="outline" class="w-full" :disabled="!track.current_target_slug" @click="openTrackInArena(track)">
                      Abrir Na Arena
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </div>
          </section>
        </div>
      </section>
    </main>
    <ProfileModal v-if="showProfile" @close="showProfile = false" />
  </div>
</template>
