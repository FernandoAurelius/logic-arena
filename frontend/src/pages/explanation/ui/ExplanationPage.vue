<script setup lang="ts">
import '@/styles/catalog.css'

import { onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { BookOpenText, LogOut, UserRound } from 'lucide-vue-next'

import { useSession } from '@/entities/session'
import { useExplanationArticle } from '@/features/explanation/article/model/useExplanationArticle'
import ProfileModal from '@/widgets/profile/ProfileModal.vue'
import { Button } from '@/shared/ui/button'
import ExplanationArticleWidget from '@/widgets/explanation/ExplanationArticleWidget.vue'

const route = useRoute()
const router = useRouter()
const session = useSession()
const showProfile = ref(false)
const explanationArticle = useExplanationArticle(session.authHeader)

async function loadExplanation() {
  await explanationArticle.loadExplanation(String(route.params.trackSlug), String(route.params.exerciseSlug))
}

async function logout() {
  session.clearSession()
  await router.push({ name: 'landing' })
}

onMounted(() => {
  void loadExplanation()
})

watch(
  () => [route.params.trackSlug, route.params.exerciseSlug],
  () => {
    void loadExplanation()
  },
)
</script>

<template>
  <div class="track-page explanation-page">
    <header class="topbar">
      <div class="topbar-left topbar-left--nav">
        <span class="brand-wordmark">LOGIC ARENA</span>
        <nav class="workspace-nav">
          <button class="workspace-nav-link" type="button" @click="router.push({ name: 'navigator' })">Navegador</button>
          <button
            class="workspace-nav-link"
            type="button"
            @click="router.push({ name: 'arena', query: { track: route.params.trackSlug, exercise: route.params.exerciseSlug } })"
          >
            Arena
          </button>
          <button class="workspace-nav-link workspace-nav-link--active" type="button">Explicação</button>
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
      </div>
    </header>

    <main class="track-workspace explanation-workspace">
      <p v-if="explanationArticle.errorMessage.value" class="notice error">{{ explanationArticle.errorMessage.value }}</p>
      <div v-else-if="explanationArticle.loading.value" class="navigator-empty-state">
        <BookOpenText :size="18" />
        <span>Carregando explicação do módulo...</span>
      </div>
      <ExplanationArticleWidget
        v-else-if="explanationArticle.explanation.value"
        :explanation="explanationArticle.explanation.value"
        @go-track="router.push({ name: 'track', params: { trackSlug: $event } })"
        @go-arena="router.push({ name: 'arena', query: { track: $event.trackSlug, exercise: $event.exerciseSlug } })"
        @go-navigator="router.push({ name: 'navigator' })"
      />
    </main>

    <ProfileModal v-if="showProfile" @close="showProfile = false" />
  </div>
</template>
