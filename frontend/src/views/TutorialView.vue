<script setup lang="ts">
import { computed, ref } from 'vue'
import { ArrowLeft, ArrowRight, BookOpenText, Cpu, Flame, History, Sparkles, Terminal } from 'lucide-vue-next'
import { useRouter } from 'vue-router'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useTheme } from '@/lib/theme'

const router = useRouter()
const theme = useTheme()

const steps = [
  {
    key: 'modules',
    title: 'Escolha um módulo',
    description: 'Comece pela lateral esquerda. Cada card representa um exercício inspirado nas aulas e listas do professor.',
    hint: 'Troque de desafio pela lista lateral antes de começar a codar.',
  },
  {
    key: 'spec',
    title: 'Leia a especificação',
    description: 'A coluna de especificação mostra enunciado, exemplos e testes visíveis para você validar a interpretação.',
    hint: 'Use os exemplos para confirmar o formato de entrada e saída antes de submeter.',
  },
  {
    key: 'editor',
    title: 'Resolva no editor',
    description: 'O editor abre vazio por padrão, como em prova. Você pode digitar sua solução completa sem código pronto.',
    hint: 'Se travar, use o botão Hints dentro da arena para receber apenas pistas curtas.',
  },
  {
    key: 'runner',
    title: 'Execute e confira',
    description: 'Ao executar, o runner testa sua solução e o console mostra o que passou, falhou ou saiu diferente do esperado.',
    hint: 'Leia o console linha por linha antes de ajustar a solução.',
  },
  {
    key: 'review',
    title: 'Revise com IA',
    description: 'Depois da submissão, você pode abrir a revisão com IA para entender melhor um erro, uma melhoria ou o raciocínio esperado.',
    hint: 'Use o chat para perguntar sobre um caso específico, não só “o que está errado?”.',
  },
]

const activeStepIndex = ref(0)
const activeStep = computed(() => steps[activeStepIndex.value])

function nextStep() {
  activeStepIndex.value = (activeStepIndex.value + 1) % steps.length
}

function previousStep() {
  activeStepIndex.value = (activeStepIndex.value - 1 + steps.length) % steps.length
}
</script>

<template>
  <div class="landing-page tutorial-page">
    <header class="landing-topbar">
      <div class="landing-brand">
        <span class="brand-wordmark">LOGIC ARENA</span>
        <span class="landing-subtitle">Ajuda Interativa</span>
      </div>
      <div class="landing-actions landing-actions--split">
        <Button variant="outline" @click="theme.toggleTheme">
          {{ theme.isDark.value ? 'Tema Claro' : 'Tema Escuro' }}
        </Button>
        <Button variant="outline" @click="router.push({ name: 'landing' })">
          Voltar
        </Button>
      </div>
    </header>

    <main class="landing-main tutorial-main">
      <section class="tutorial-hero">
        <div>
          <p class="eyebrow">Ajuda</p>
          <h1 class="landing-hero-title tutorial-title">Aprenda a usar a arena sem adivinhação.</h1>
          <p class="landing-hero-description">
            Este guia mostra os componentes principais da plataforma, como interpretar a interface e quando usar cada recurso durante a prática.
          </p>
        </div>
      </section>

      <section class="tutorial-grid">
        <Card class="tutorial-step-card">
          <CardHeader>
            <p class="eyebrow">Passo {{ activeStepIndex + 1 }}/{{ steps.length }}</p>
            <CardTitle>{{ activeStep.title }}</CardTitle>
            <CardDescription>{{ activeStep.description }}</CardDescription>
          </CardHeader>
          <CardContent class="tutorial-step-content">
            <div class="hint-block">
              <p class="section-label">O que observar</p>
              <p>{{ activeStep.hint }}</p>
            </div>

            <div class="tutorial-controls">
              <Button variant="outline" @click="previousStep">
                <ArrowLeft :size="16" />
                Anterior
              </Button>
              <Button @click="nextStep">
                Próximo
                <ArrowRight :size="16" />
              </Button>
            </div>

            <div class="tutorial-step-list">
              <button
                v-for="(step, index) in steps"
                :key="step.key"
                class="tutorial-step-chip"
                :class="{ active: index === activeStepIndex }"
                @click="activeStepIndex = index"
              >
                {{ index + 1 }}. {{ step.title }}
              </button>
            </div>
          </CardContent>
        </Card>

        <Card class="tutorial-preview-card">
          <CardHeader>
            <p class="eyebrow">Simulação</p>
            <CardTitle>Mapa da interface</CardTitle>
            <CardDescription>O destaque muda conforme o passo selecionado.</CardDescription>
          </CardHeader>
          <CardContent class="tutorial-shell">
            <div class="tutorial-shell-topbar">
              <div class="tutorial-shell-brand">LOGIC ARENA</div>
              <div class="tutorial-shell-topbar-actions">
                <span class="tutorial-shell-button">Tema</span>
                <span class="tutorial-shell-button">Sair</span>
              </div>
            </div>
            <div class="tutorial-shell-body">
              <div class="tutorial-shell-sidebar" :class="{ active: activeStep.key === 'modules' }">
                <div class="tutorial-shell-card tutorial-shell-card--operator">
                  <Cpu :size="18" />
                  <span>Operator</span>
                </div>
                <div class="tutorial-shell-card">
                  <BookOpenText :size="16" />
                  <span>Core Modules</span>
                </div>
                <div class="tutorial-shell-card">
                  <History :size="16" />
                  <span>History</span>
                </div>
              </div>

              <div class="tutorial-shell-workspace">
                <div class="tutorial-shell-spec" :class="{ active: activeStep.key === 'spec' }">
                  <strong>Technical Specification</strong>
                  <span>Enunciado + exemplos + testes visíveis</span>
                </div>
                <div class="tutorial-shell-editor" :class="{ active: activeStep.key === 'editor' }">
                  <div class="tutorial-shell-editor-top">
                    <span>Editor</span>
                    <div class="tutorial-shell-pills">
                      <span>Hints</span>
                      <span>Executar</span>
                    </div>
                  </div>
                  <div class="tutorial-shell-editor-body">
                    <Flame :size="18" />
                    <span>Canvas de código vazio por padrão</span>
                  </div>
                </div>
                <div class="tutorial-shell-bottom-grid">
                  <div class="tutorial-shell-console" :class="{ active: activeStep.key === 'runner' }">
                    <Terminal :size="16" />
                    <span>Console / runner</span>
                  </div>
                  <div class="tutorial-shell-review" :class="{ active: activeStep.key === 'review' }">
                    <Sparkles :size="16" />
                    <span>Revisar com IA</span>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </section>
    </main>
  </div>
</template>
