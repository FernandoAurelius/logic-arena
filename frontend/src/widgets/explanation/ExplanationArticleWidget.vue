<script setup lang="ts">
import { ArrowLeft, Play, Route } from 'lucide-vue-next'

import type { ExerciseExplanation } from '@/entities/explanation'
import { renderMarkdown } from '@/shared/markdown/renderer'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

defineProps<{
  explanation: ExerciseExplanation
}>()

const emit = defineEmits<{
  (event: 'go-track', trackSlug: string): void
  (event: 'go-arena', payload: { trackSlug: string; exerciseSlug: string }): void
  (event: 'go-navigator'): void
}>()
</script>

<template>
  <div class="explanation-layout">
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
            <Button variant="outline" class="w-full" @click="emit('go-track', explanation.track_slug)">
              <ArrowLeft :size="16" />
              Voltar à trilha
            </Button>
            <Button class="w-full" @click="emit('go-arena', { trackSlug: explanation.track_slug, exerciseSlug: explanation.exercise_slug })">
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
          <Button variant="outline" class="w-full" @click="emit('go-navigator')">
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
</template>
