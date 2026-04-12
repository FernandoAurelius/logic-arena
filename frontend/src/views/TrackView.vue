<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { BookOpenText, LogOut, UserRound } from 'lucide-vue-next'

import { catalogApi } from '@/entities/catalog/api/catalog.api'
import type { TrackDetail } from '@/entities/track'
import { useSession } from '@/entities/session'
import ProfileModal from '@/components/theme/ProfileModal.vue'
import { Button } from '@/components/ui/button'
import TrackRoadmapWidget from '@/widgets/track/TrackRoadmapWidget.vue'

const route = useRoute()
const router = useRouter()
const session = useSession()

const track = ref<TrackDetail | null>(null)
const loading = ref(false)
const errorMessage = ref('')
const showProfile = ref(false)

function openExplanation(exerciseSlug: string) {
  if (!track.value) return
  void router.push({
    name: 'track-explanation',
    params: {
      trackSlug: track.value.slug,
      exerciseSlug,
    },
  })
}

function openArena(exerciseSlug?: string) {
  void router.push({
    name: 'arena',
    query: exerciseSlug ? { exercise: exerciseSlug, track: track.value?.slug } : { track: track.value?.slug },
  })
}

async function loadTrack() {
  loading.value = true
  errorMessage.value = ''

  try {
    track.value = await catalogApi.getTrackDetail(route.params.trackSlug as string, session.authHeader() ?? undefined)
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
          <TrackRoadmapWidget :track="track" @open-explanation="openExplanation" @open-arena="openArena" />
        </div>
      </div>
    </main>

    <ProfileModal v-if="showProfile" @close="showProfile = false" />
  </div>
</template>
