<script setup lang="ts">
import '@/styles/catalog.css'
import { useRouter } from 'vue-router'
import { LogOut, Route, UserRound } from 'lucide-vue-next'

import ThemePicker from '@/widgets/profile/ThemePicker.vue'
import { Button } from '@/shared/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/shared/ui/card'
import { useSession } from '@/entities/session'

const router = useRouter()
const session = useSession()

async function logout() {
  session.clearSession()
  await router.push({ name: 'landing' })
}
</script>

<template>
  <div class="navigator-page">
    <header class="topbar">
      <div class="topbar-left topbar-left--nav">
        <span class="brand-wordmark">LOGIC ARENA</span>
        <nav class="workspace-nav">
          <button class="workspace-nav-link" type="button" @click="router.push({ name: 'navigator' })">Navegador</button>
          <button class="workspace-nav-link" type="button" @click="router.push({ name: 'arena' })">Arena</button>
          <button class="workspace-nav-link workspace-nav-link--active" type="button">Perfil</button>
        </nav>
      </div>
      <div class="topbar-right">
        <div class="topbar-actions">
          <Button variant="outline" size="sm" @click="router.push({ name: 'navigator' })">
            <Route :size="14" />
            Voltar
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

    <main class="profile-workspace">
      <section class="profile-grid">
        <Card class="profile-card">
          <CardHeader>
            <p class="eyebrow">Perfil do operador</p>
            <CardTitle>Personalização</CardTitle>
            <CardDescription>
              Centralize aqui preferências visuais da sua estação, sem poluir as telas de prática.
            </CardDescription>
          </CardHeader>
          <CardContent class="profile-card-content">
            <div class="profile-identity">
              <div class="operator-icon operator-icon--large">
                <UserRound :size="20" />
              </div>
              <div>
                <strong>{{ session.currentUser.value?.nickname ?? 'operador' }}</strong>
                <p>Nível {{ session.currentUser.value?.level ?? 1 }} · {{ session.currentUser.value?.xp_total ?? 0 }} XP</p>
              </div>
            </div>
            <ThemePicker />
          </CardContent>
        </Card>
      </section>
    </main>
  </div>
</template>
