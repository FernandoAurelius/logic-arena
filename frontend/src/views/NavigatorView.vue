<script setup lang="ts">
import '@/styles/catalog.css'

import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { LogOut, UserRound } from 'lucide-vue-next'

import type { TrackSummary } from '@/entities/catalog'
import { useSession } from '@/entities/session'
import { useNavigatorCatalog } from '@/features/navigator/catalog/model/useNavigatorCatalog'
import ProfileModal from '@/components/theme/ProfileModal.vue'
import { Button } from '@/components/ui/button'
import NavigatorCatalogWidget from '@/widgets/navigator/NavigatorCatalogWidget.vue'

const router = useRouter()
const session = useSession()
const showProfile = ref(false)
const navigatorCatalog = useNavigatorCatalog(session.authHeader)

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

async function logout() {
  session.clearSession()
  await router.push({ name: 'landing' })
}

onMounted(() => {
  void navigatorCatalog.loadNavigator()
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

    <NavigatorCatalogWidget
      :modules="navigatorCatalog.modules.value"
      :visible-modules="navigatorCatalog.visibleModules.value"
      :visible-track-count="navigatorCatalog.visibleTrackCount.value"
      :recommended-track="navigatorCatalog.recommendedTrack.value"
      :recommended-module="navigatorCatalog.recommendedModule.value"
      :loading="navigatorCatalog.loading.value"
      :error-message="navigatorCatalog.errorMessage.value"
      :active-module="navigatorCatalog.activeModule.value"
      :active-status="navigatorCatalog.activeStatus.value"
      :progress-label="navigatorCatalog.progressLabel"
      :status-tone="navigatorCatalog.statusTone"
      @update:active-module="navigatorCatalog.activeModule.value = $event"
      @update:active-status="navigatorCatalog.activeStatus.value = $event"
      @open-track="openTrack"
      @open-track-in-arena="openTrackInArena"
      @open-arena="router.push({ name: 'arena' })"
    />

    <ProfileModal v-if="showProfile" @close="showProfile = false" />
  </div>
</template>
