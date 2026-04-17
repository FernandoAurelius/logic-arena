<script setup lang="ts">
import { computed, ref } from 'vue'
import { ArrowLeft, ChevronLeft, ChevronRight, Play, Route } from 'lucide-vue-next'

import type { ExerciseExplanation } from '@/entities/explanation'
import { renderMarkdown } from '@/shared/markdown/renderer'
import { Button } from '@/shared/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/shared/ui/card'

const props = defineProps<{
  explanation: ExerciseExplanation
}>()

const emit = defineEmits<{
  (event: 'go-track', trackSlug: string): void
  (event: 'go-arena', payload: { trackSlug: string; exerciseSlug: string }): void
  (event: 'go-navigator'): void
}>()

const sidebarCollapsed = ref(false)
const isObjectiveReview = computed(() => props.explanation.presentation_mode === 'objective_review')
const sidebarSections = computed(() => {
  if (isObjectiveReview.value) {
    return [
      { id: 'ideia-central', label: 'Ideia central' },
      { id: 'identificar-correta', label: 'Como identificar a correta' },
      { id: 'alternativa-correta', label: 'Alternativa correta' },
      { id: 'distratores', label: 'Distratores' },
      { id: 'conceitos', label: 'Conceitos do módulo' },
      { id: 'erros', label: 'Erros comuns' },
      { id: 'avaliacao', label: 'Como isso cai na prova' },
    ]
  }

  return [
    { id: 'visao-geral', label: 'Visão geral' },
    { id: 'leitura', label: 'Como ler' },
    { id: 'implementacao', label: 'Implementação' },
    { id: 'conceitos', label: 'Conceitos' },
    { id: 'exemplos', label: 'Exemplos' },
    { id: 'avaliacao', label: 'Avaliação' },
  ]
})
</script>

<template>
  <div class="explanation-layout" :class="{ 'explanation-layout--collapsed': sidebarCollapsed }">
    <aside class="explanation-sidebar">
      <div class="explanation-sidebar__rail">
        <Button
          variant="outline"
          size="icon"
          class="explanation-sidebar__collapse"
          @click="sidebarCollapsed = !sidebarCollapsed"
        >
          <ChevronLeft v-if="!sidebarCollapsed" :size="16" />
          <ChevronRight v-else :size="16" />
        </Button>
      </div>

      <div v-if="!sidebarCollapsed" class="explanation-sidebar__content">
        <Card class="track-summary-card">
          <CardHeader>
            <p class="eyebrow">Questão</p>
            <CardTitle>{{ explanation.exercise_title }}</CardTitle>
            <CardDescription>{{ explanation.exercise_type_label }} · {{ explanation.estimated_time_minutes }} min</CardDescription>
          </CardHeader>
          <CardContent class="track-summary-body">
            <p class="track-summary-copy">{{ explanation.concept_summary || explanation.learning_goal }}</p>
            <div class="track-summary-actions">
              <Button variant="outline" class="w-full" @click="emit('go-track', explanation.track_slug)">
                <ArrowLeft :size="16" />
                Voltar à trilha
              </Button>
              <Button class="w-full" @click="emit('go-arena', { trackSlug: explanation.track_slug, exerciseSlug: explanation.exercise_slug })">
                <Play :size="16" />
                Abrir questão
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
            <nav class="explanation-sidebar__nav">
              <a
                v-for="section in sidebarSections"
                :key="section.id"
                class="explanation-sidebar__nav-link"
                :href="`#${section.id}`"
              >
                {{ section.label }}
              </a>
            </nav>
            <Button variant="outline" class="w-full" @click="emit('go-navigator')">
              <Route :size="16" />
              Voltar ao Navegador
            </Button>
          </CardContent>
        </Card>
      </div>
    </aside>

    <section class="explanation-article">
      <Card class="explanation-article-card">
        <CardContent class="explanation-article-body">
          <article class="explanation-markdown">
            <p class="eyebrow">Documentação / Explicação</p>
            <h1>{{ explanation.exercise_title }}</h1>
            <p class="track-summary-copy">{{ explanation.learning_goal }}</p>

            <template v-if="isObjectiveReview">
              <section id="ideia-central" class="explanation-section">
                <h2>Ideia central da questão</h2>
                <div class="markdown-body" v-html="renderMarkdown(explanation.question_focus || explanation.concept_focus_markdown)"></div>
              </section>

              <section id="identificar-correta" class="explanation-section">
                <h2>Como identificar a correta</h2>
                <div class="markdown-body" v-html="renderMarkdown(explanation.reading_strategy_markdown)"></div>
              </section>

              <section id="alternativa-correta" class="explanation-section" v-if="explanation.answer_rationale">
                <h2>Alternativa correta e por quê</h2>
                <div class="markdown-body" v-html="renderMarkdown(explanation.answer_rationale)"></div>
              </section>

              <section id="distratores" class="explanation-section" v-if="explanation.distractor_rationales.length">
                <h2>Como eliminar os distratores</h2>
                <div class="explanation-distractors">
                  <article
                    v-for="option in explanation.distractor_rationales"
                    :key="`${option.marker}-${option.key}`"
                    class="explanation-distractor-card"
                  >
                    <h3>{{ option.marker }}. {{ option.text }}</h3>
                    <p>{{ option.explanation || 'Ela parece plausível, mas não responde exatamente ao que o enunciado pede.' }}</p>
                  </article>
                </div>
              </section>

              <section id="conceitos" class="explanation-section">
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

              <section id="erros" class="explanation-section">
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

              <section id="avaliacao" class="explanation-section">
                <h2>O que essa questão queria medir</h2>
                <div class="markdown-body" v-html="renderMarkdown(explanation.assessment_notes_markdown)"></div>
              </section>
            </template>

            <template v-else>
              <section id="visao-geral" class="explanation-section">
                <h2>Visão geral do conceito</h2>
                <div class="markdown-body" v-html="renderMarkdown(explanation.concept_focus_markdown)"></div>
              </section>

              <section id="leitura" class="explanation-section">
                <h2>Como ler esse tipo de problema</h2>
                <div class="markdown-body" v-html="renderMarkdown(explanation.reading_strategy_markdown)"></div>
              </section>

              <section id="implementacao" class="explanation-section">
                <h2>Como transformar isso em código</h2>
                <div class="markdown-body" v-html="renderMarkdown(explanation.implementation_strategy_markdown)"></div>
              </section>

              <section id="conceitos" class="explanation-section">
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

              <section id="exemplos" class="explanation-section">
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

              <section id="avaliacao" class="explanation-section">
                <h2>Como isso costuma ser cobrado</h2>
                <div class="markdown-body" v-html="renderMarkdown(explanation.assessment_notes_markdown)"></div>
              </section>
            </template>
          </article>
        </CardContent>
      </Card>
    </section>
  </div>
</template>

<style scoped>
.explanation-sidebar {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 0.85rem;
  align-items: start;
}

.explanation-sidebar__rail {
  position: sticky;
  top: 0;
}

.explanation-sidebar__collapse {
  height: 2.5rem;
  width: 2.5rem;
}

.explanation-sidebar__content {
  display: grid;
  gap: 1rem;
}

.explanation-sidebar__nav {
  display: grid;
  gap: 0.5rem;
}

.explanation-sidebar__nav-link {
  display: block;
  padding: 0.65rem 0.8rem;
  border: 1px dashed var(--outline);
  font-family: 'Space Grotesk', sans-serif;
  font-size: 0.85rem;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--on-surface);
}

.explanation-sidebar__nav-link:hover {
  border-color: var(--primary);
  color: var(--primary);
}

.explanation-distractors {
  display: grid;
  gap: 0.9rem;
}

.explanation-distractor-card {
  padding: 1rem 1.05rem;
  border: 1px solid var(--outline);
  background: color-mix(in srgb, var(--surface) 90%, white);
}

.explanation-layout--collapsed {
  grid-template-columns: 4.5rem minmax(0, 1fr);
}

@media (max-width: 960px) {
  .explanation-layout--collapsed {
    grid-template-columns: minmax(0, 1fr);
  }

  .explanation-sidebar {
    grid-template-columns: auto 1fr;
  }
}
</style>
