<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js/lib/core'
import python from 'highlight.js/lib/languages/python'
import javascript from 'highlight.js/lib/languages/javascript'
import json from 'highlight.js/lib/languages/json'
import { ArrowLeft, BookOpenText, LogOut, Play, Route, UserRound } from 'lucide-vue-next'
import type { infer as ZodInfer } from 'zod'

import { schemas } from '@/lib/api/generated'
import { useSession } from '@/lib/session'
import ProfileModal from '@/components/theme/ProfileModal.vue'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

type ExerciseExplanation = ZodInfer<typeof schemas.ExerciseExplanationSchema>

hljs.registerLanguage('python', python)
hljs.registerLanguage('javascript', javascript)
hljs.registerLanguage('json', json)

const route = useRoute()
const router = useRouter()
const session = useSession()

const explanation = ref<ExerciseExplanation | null>(null)
const loading = ref(false)
const errorMessage = ref('')
const showProfile = ref(false)

const markdown = new MarkdownIt({
  html: false,
  breaks: true,
  linkify: true,
  highlight(code, language) {
    const normalizedLanguage = language?.trim().toLowerCase()
    if (normalizedLanguage && hljs.getLanguage(normalizedLanguage)) {
      return `<pre class="hljs"><code>${hljs.highlight(code, { language: normalizedLanguage }).value}</code></pre>`
    }
    return `<pre class="hljs"><code>${hljs.highlightAuto(code).value}</code></pre>`
  },
})

function renderMarkdown(content: string) {
  return markdown.render(content)
}

async function loadExplanation() {
  loading.value = true
  errorMessage.value = ''

  try {
    const response = await fetch(
      `${import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'}/api/catalog/tracks/${route.params.trackSlug}/explanations/${route.params.exerciseSlug}`,
      {
        headers: {
          Authorization: session.authHeader() ?? '',
        },
      },
    )

    if (!response.ok) {
      throw new Error(`Falha ao carregar explanation: ${response.status}`)
    }

    explanation.value = (await response.json()) as ExerciseExplanation
  } catch (error) {
    console.error(error)
    errorMessage.value = 'Não foi possível carregar a explanation deste módulo.'
  } finally {
    loading.value = false
  }
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
      <p v-if="errorMessage" class="notice error">{{ errorMessage }}</p>
      <div v-else-if="loading" class="navigator-empty-state">
        <BookOpenText :size="18" />
        <span>Carregando explicação do módulo...</span>
      </div>
      <div v-else-if="explanation" class="explanation-layout">
        <aside class="explanation-sidebar">
          <Card class="track-summary-card">
            <CardHeader>
              <p class="eyebrow">Módulo</p>
              <CardTitle>{{ explanation.exercise_title }}</CardTitle>
              <CardDescription>{{ explanation.exercise_type_label }} · {{ explanation.estimated_time_minutes }} min</CardDescription>
            </CardHeader>
            <CardContent class="track-summary-body">
              <p class="track-summary-copy">{{ explanation.concept_summary }}</p>
              <div class="track-summary-actions">
                <Button variant="outline" class="w-full" @click="router.push({ name: 'track', params: { trackSlug: explanation.track_slug } })">
                  <ArrowLeft :size="16" />
                  Voltar à trilha
                </Button>
                <Button class="w-full" @click="router.push({ name: 'arena', query: { track: explanation.track_slug, exercise: explanation.exercise_slug } })">
                  <Play :size="16" />
                  Iniciar exercício
                </Button>
              </div>
            </CardContent>
          </Card>

          <Card class="track-summary-card">
            <CardHeader>
              <p class="eyebrow">Contexto</p>
              <CardTitle>{{ explanation.module_name ?? explanation.track_name }}</CardTitle>
              <CardDescription>{{ explanation.track_name }} · {{ explanation.level_label }}</CardDescription>
            </CardHeader>
            <CardContent class="track-summary-body">
              <p class="track-summary-copy">{{ explanation.track_goal }}</p>
                <Button variant="outline" class="w-full" @click="router.push({ name: 'navigator' })">
                  <Route :size="16" />
                  Voltar ao Navegador
                </Button>
              </CardContent>
            </Card>
        </aside>

        <section class="explanation-article">
          <Card class="explanation-article-card">
            <CardContent class="explanation-article-body">
              <article class="explanation-markdown">
                <p class="eyebrow">Documentação / Explicação</p>
                <h1>{{ explanation.exercise_title }}</h1>
                <p class="track-summary-copy">{{ explanation.learning_goal }}</p>

                <section class="explanation-section">
                  <h2>Visão geral do conceito</h2>
                  <div class="markdown-body" v-html="renderMarkdown(explanation.concept_focus_markdown)"></div>
                </section>

                <section class="explanation-section">
                  <h2>Como ler esse tipo de problema</h2>
                  <div class="markdown-body" v-html="renderMarkdown(explanation.reading_strategy_markdown)"></div>
                </section>

                <section class="explanation-section">
                  <h2>Como transformar isso em código</h2>
                  <div class="markdown-body" v-html="renderMarkdown(explanation.implementation_strategy_markdown)"></div>
                </section>

                <section class="explanation-section">
                  <h2>Conceitos do módulo</h2>
                  <div class="explanation-concepts">
                    <article v-for="concept in explanation.concepts" :key="concept.title" class="explanation-concept-card">
                      <h3>{{ concept.title }}</h3>
                      <p>{{ concept.explanation_text }}</p>
                      <p><strong>Por que importa:</strong> {{ concept.why_it_matters }}</p>
                      <p><strong>Erro comum:</strong> {{ concept.common_mistake }}</p>
                    </article>
                  </div>
                </section>

                <section class="explanation-section">
                  <h2>Exemplos de código obrigatórios</h2>
                  <div class="explanation-examples">
                    <article v-for="example in explanation.code_examples" :key="example.title" class="explanation-example-card">
                      <h3>{{ example.title }}</h3>
                      <p>{{ example.rationale }}</p>
                      <div class="markdown-body" v-html="renderMarkdown(`\`\`\`${example.language}\n${example.code}\n\`\`\``)"></div>
                    </article>
                  </div>
                </section>

                <section class="explanation-section">
                  <h2>Erros que mais derrubam ponto</h2>
                  <ul class="explanation-list">
                    <li v-for="item in explanation.common_mistakes" :key="item">{{ item }}</li>
                  </ul>
                </section>

                <section class="explanation-section">
                  <h2>Checklist de domínio</h2>
                  <ul class="explanation-list">
                    <li v-for="item in explanation.mastery_checklist" :key="item">{{ item }}</li>
                  </ul>
                </section>

                <section class="explanation-section">
                  <h2>Pré-requisitos</h2>
                  <ul class="explanation-list">
                    <li v-for="item in explanation.prerequisites" :key="item">{{ item }}</li>
                  </ul>
                </section>

                <section class="explanation-section">
                  <h2>Como isso costuma ser cobrado</h2>
                  <div class="markdown-body" v-html="renderMarkdown(explanation.assessment_notes_markdown)"></div>
                </section>
              </article>
            </CardContent>
          </Card>
        </section>
      </div>
    </main>

    <ProfileModal v-if="showProfile" @close="showProfile = false" />
  </div>
</template>
