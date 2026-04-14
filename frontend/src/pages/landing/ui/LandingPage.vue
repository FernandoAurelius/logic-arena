<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowRight, Cpu, History, Moon, Play, Sparkles, Sun } from 'lucide-vue-next'

import LoginModal from '@/features/auth/login/ui/LoginModal.vue'
import { Button } from '@/shared/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/shared/ui/card'
import { useSession } from '@/entities/session'
import { useTheme } from '@/lib/theme'

const router = useRouter()
const session = useSession()
const theme = useTheme()
const showLogin = ref(false)

const highlights = [
  {
    title: 'Editor real',
    description: 'Resolva questões práticas num canvas com Monaco e sensação de IDE leve.',
    icon: Cpu,
  },
  {
    title: 'Runner isolado',
    description: 'Execute código Python com testes reais, console e critérios de aprovação.',
    icon: Play,
  },
  {
    title: 'Feedback com IA',
    description: 'Receba comentários objetivos da Gemini após cada submissão.',
    icon: Sparkles,
  },
  {
    title: 'Histórico persistido',
    description: 'Acompanhe tentativas, acertos e evolução por exercício.',
    icon: History,
  },
]

async function handlePrimaryAction() {
  await session.initSession()
  if (session.isAuthenticated.value) {
    await router.push({ name: 'navigator' })
    return
  }
  showLogin.value = true
}
</script>

<template>
  <div class="landing-page">
    <header class="landing-topbar">
      <div class="landing-brand">
        <span class="brand-wordmark">LOGIC ARENA</span>
        <span class="landing-subtitle">Logic Arena</span>
      </div>
      <div class="landing-actions landing-actions--split">
        <Button variant="outline" class="landing-action-button" @click="theme.toggleTheme">
          <Sun v-if="theme.isDark.value" :size="16" />
          <Moon v-else :size="16" />
          {{ theme.isDark.value ? 'Tema Claro' : 'Tema Escuro' }}
        </Button>
        <Button variant="outline" class="landing-action-button" @click="router.push({ name: 'tutorial' })">
          Ajuda
        </Button>
        <Button variant="outline" class="landing-action-button" @click="handlePrimaryAction">
          {{ session.isAuthenticated.value ? 'Ir Para A Arena' : 'Entrar' }}
        </Button>
      </div>
    </header>

    <main class="landing-main">
      <section class="landing-hero-grid">
        <div class="landing-copy-block">
          <p class="eyebrow">Simulador de Avaliação Prática</p>
          <h1 class="landing-hero-title">Treine lógica de programação como se estivesse na prova.</h1>
          <p class="landing-hero-description">
            Uma plataforma interna e enxuta para praticar exercícios no estilo cobrado em sala, com execução real,
            correção por testes e feedback imediato.
          </p>
          <div class="landing-cta-row">
            <Button @click="handlePrimaryAction">
              Entrar Na Plataforma
              <ArrowRight :size="16" />
            </Button>
            <Button variant="outline" @click="router.push({ name: 'tutorial' })">
              Ver Tutorial
            </Button>
          </div>
        </div>

        <Card class="landing-preview-card">
          <CardHeader>
            <p class="eyebrow">Preview</p>
            <CardTitle>O que acontece depois do login</CardTitle>
            <CardDescription>
              Você entra no Navigator autenticado para escolher a trilha certa e daí segue para a arena com contexto.
            </CardDescription>
          </CardHeader>
          <CardContent class="preview-shell">
            <div class="preview-topline">
              <span>COMPILER</span>
              <span>ARENA</span>
              <span>RUNNER</span>
            </div>
            <div class="preview-grid">
              <div class="preview-sidebar">
                <div class="preview-mini-card"></div>
                <div class="preview-mini-card"></div>
                <div class="preview-mini-card"></div>
              </div>
              <div class="preview-workspace">
                <div class="preview-header"></div>
                <div class="preview-editor"></div>
                <div class="preview-console"></div>
              </div>
            </div>
          </CardContent>
        </Card>
      </section>

      <section class="landing-features-grid">
        <Card v-for="item in highlights" :key="item.title" class="landing-feature-card">
          <CardHeader>
            <component :is="item.icon" :size="18" />
            <CardTitle>{{ item.title }}</CardTitle>
          </CardHeader>
          <CardContent>
            <p class="landing-feature-copy">{{ item.description }}</p>
          </CardContent>
        </Card>
      </section>
    </main>

    <LoginModal v-if="showLogin" @close="showLogin = false" />
  </div>
</template>
