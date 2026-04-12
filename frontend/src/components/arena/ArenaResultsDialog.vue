<script setup lang="ts">
import { computed } from 'vue'
import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js/lib/core'
import python from 'highlight.js/lib/languages/python'
import javascript from 'highlight.js/lib/languages/javascript'
import json from 'highlight.js/lib/languages/json'
import { Bot, FileTerminal, LoaderCircle, MessageSquareText, Send, Terminal, TestTubeDiagonal } from 'lucide-vue-next'
import type { infer as ZodInfer } from 'zod'

import { schemas } from '@/lib/api/generated'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

type Submission = ZodInfer<typeof schemas.SubmissionSchema>
type ReviewChatMessage = ZodInfer<typeof schemas.ReviewChatMessageSchema>
type ProgressReward = ZodInfer<typeof schemas.ProgressRewardSchema>
type FeedbackPayload = ZodInfer<typeof schemas.FeedbackPayloadSchema>

type ResultsTab = 'saida' | 'testes' | 'revisao' | 'chat'

const props = withDefaults(defineProps<{
  open: boolean
  tab: ResultsTab
  activeExerciseTitle?: string
  submission: Submission | null
  consoleLines?: string[]
  submissionOutcomeTone?: string
  submissionOutcomeTitle?: string
  submissionOutcomeCopy?: string
  rewardSummary?: string
  progressRewards?: ProgressReward[]
  feedbackPayload?: FeedbackPayload | null
  chatMessages?: ReviewChatMessage[]
  chatInput?: string
  isChatBusy?: boolean
}>(), {
  activeExerciseTitle: '',
  consoleLines: () => [],
  submissionOutcomeTone: 'idle',
  submissionOutcomeTitle: 'Aguardando execução',
  submissionOutcomeCopy: '',
  rewardSummary: '',
  progressRewards: () => [],
  feedbackPayload: null,
  chatMessages: () => [],
  chatInput: '',
  isChatBusy: false,
})

const emit = defineEmits<{
  (event: 'update:open', value: boolean): void
  (event: 'update:tab', value: ResultsTab): void
  (event: 'update:chatInput', value: string): void
  (event: 'send-chat'): void
}>()

hljs.registerLanguage('python', python)
hljs.registerLanguage('javascript', javascript)
hljs.registerLanguage('json', json)

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

const openModel = computed({
  get: () => props.open,
  set: (value: boolean) => emit('update:open', value),
})

const tabModel = computed({
  get: () => props.tab,
  set: (value: string | number) => emit('update:tab', value as ResultsTab),
})

const chatInputModel = computed({
  get: () => props.chatInput,
  set: (value: string) => emit('update:chatInput', value),
})

const feedbackSummary = computed(() => props.feedbackPayload?.summary ?? props.submission?.feedback ?? 'Sem revisão disponível.')
const isFeedbackLoading = computed(() => props.submission?.feedback_status === 'pending')
const hasStructuredFeedback = computed(() =>
  Boolean(
    props.feedbackPayload?.summary
    || props.feedbackPayload?.strengths?.length
    || props.feedbackPayload?.issues?.length
    || props.feedbackPayload?.next_steps?.length,
  ),
)

function renderMessage(content: string) {
  return markdown.render(content)
}

function traduzirStatusExecucao(status?: string) {
  switch (status) {
    case 'passed':
      return 'Aprovada'
    case 'failed':
      return 'Reprovada'
    case 'error':
      return 'Erro'
    case 'pending':
      return 'Pendente'
    default:
      return 'Inativa'
  }
}

function traduzirStatusFeedback(status?: string) {
  switch (status) {
    case 'ready':
      return 'Pronto'
    case 'pending':
      return 'Analisando'
    case 'error':
      return 'Erro'
    default:
      return 'Sem revisão'
  }
}

function consoleTagClass(line: string) {
  if (line.includes('PASSOU')) return 'tag pass'
  if (line.includes('FALHOU')) return 'tag fail'
  return 'tag exec'
}

function consoleTagLabel(line: string) {
  if (line.includes('PASSOU')) return '[PASS]'
  if (line.includes('FALHOU')) return '[FAIL]'
  return '[EXEC]'
}
</script>

<template>
  <Dialog v-model:open="openModel">
    <DialogContent v-if="submission" class="results-dialog-content">
      <DialogHeader>
        <DialogTitle>Central da execução</DialogTitle>
        <DialogDescription>
          {{ activeExerciseTitle }} · {{ submission.passed_tests }}/{{ submission.total_tests }} testes
        </DialogDescription>
      </DialogHeader>

      <div class="results-dialog-topline">
        <Badge>{{ traduzirStatusExecucao(submission.status) }}</Badge>
        <Badge variant="outline">{{ submission.xp_awarded > 0 ? `+${submission.xp_awarded} XP` : '0 XP' }}</Badge>
        <Badge variant="outline">Nível {{ submission.user_progress.level }}</Badge>
        <Badge variant="outline">{{ traduzirStatusFeedback(submission.feedback_status) }}</Badge>
        <div v-if="isFeedbackLoading" class="results-topline-loader">
          <LoaderCircle :size="14" />
          <span>Analisando com IA...</span>
        </div>
      </div>

        <Tabs v-model:model-value="tabModel" class="results-tabs">
          <TabsList class="results-tabs-list">
            <TabsTrigger value="saida" class="results-tabs-trigger">
              <FileTerminal :size="15" />
              Saída
            </TabsTrigger>
            <TabsTrigger value="testes" class="results-tabs-trigger">
              <TestTubeDiagonal :size="15" />
              Testes
            </TabsTrigger>
            <TabsTrigger value="revisao" class="results-tabs-trigger">
              <Bot :size="15" />
              Revisão da IA
            </TabsTrigger>
            <TabsTrigger value="chat" class="results-tabs-trigger">
              <MessageSquareText :size="15" />
              Chat
            </TabsTrigger>
          </TabsList>

        <TabsContent value="saida" class="results-tab-panel">
          <div class="results-panel-grid">
            <Card class="outcome-card" :data-tone="submissionOutcomeTone">
              <CardHeader>
                <div class="feedback-header">
                  <div>
                    <p class="eyebrow">Resultado da rodada</p>
                    <CardTitle>{{ submissionOutcomeTitle }}</CardTitle>
                  </div>
                </div>
              </CardHeader>
              <CardContent class="outcome-grid">
                <div class="outcome-block">
                  <p class="section-label">Execução</p>
                  <strong>{{ submission.passed_tests }}/{{ submission.total_tests }} testes</strong>
                  <p>{{ submissionOutcomeCopy }}</p>
                </div>
                <div class="outcome-block">
                  <p class="section-label">Progressão</p>
                  <strong>{{ rewardSummary }}</strong>
                  <p>
                    XP total: {{ submission.user_progress.xp_total }} · faltam
                    {{ submission.user_progress.xp_to_next_level }} XP para o próximo nível
                  </p>
                </div>
              </CardContent>
            </Card>

            <Card class="console-card">
              <CardHeader class="console-header">
                <div class="console-heading">
                  <Terminal :size="16" />
                  <CardTitle>Console de execução</CardTitle>
                </div>
                <Badge variant="outline" class="console-status-badge">Saída bruta</Badge>
              </CardHeader>
              <CardContent class="console-content">
                <div class="console-body">
                  <div v-for="(line, index) in consoleLines" :key="`${index}-${line}`" class="console-line">
                    <span class="console-time">{{ String(index).padStart(2, '0') }}:42</span>
                    <span :class="consoleTagClass(line)">
                      {{ consoleTagLabel(line) }}
                    </span>
                    <span>{{ line }}</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="testes" class="results-tab-panel">
          <Card>
            <CardHeader>
              <CardTitle>Resultado dos testes</CardTitle>
              <CardDescription>Diagnóstico detalhado de cada caso executado.</CardDescription>
            </CardHeader>
            <CardContent class="test-results-list">
              <article v-for="result in submission.results" :key="result.index" class="test-result-card" :data-passed="result.passed">
                <div class="test-result-header">
                  <strong>Teste {{ result.index }}</strong>
                  <Badge :variant="result.passed ? 'default' : 'outline'">
                    {{ result.passed ? 'Passou' : 'Falhou' }}
                  </Badge>
                </div>
                <div class="test-result-grid">
                  <div>
                    <p class="section-label">Entrada</p>
                    <code>{{ result.input_data }}</code>
                  </div>
                  <div>
                    <p class="section-label">Esperado</p>
                    <code>{{ result.expected_output }}</code>
                  </div>
                  <div>
                    <p class="section-label">Obtido</p>
                    <code>{{ result.actual_output || 'Sem saída' }}</code>
                  </div>
                  <div v-if="result.stderr">
                    <p class="section-label">Erro</p>
                    <code>{{ result.stderr }}</code>
                  </div>
                </div>
              </article>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="revisao" class="results-tab-panel">
          <Card v-if="isFeedbackLoading" class="feedback-card feedback-card--loading">
            <CardHeader>
              <div class="feedback-header">
                <div>
                  <p class="eyebrow">Revisão automática</p>
                  <CardTitle>Analisando sua solução</CardTitle>
                  <CardDescription>
                    A IA está consolidando pontos fortes, ajustes e próximos passos desta submissão.
                  </CardDescription>
                </div>
                <LoaderCircle class="feedback-loader" :size="22" />
              </div>
            </CardHeader>
            <CardContent class="feedback-loading-shell">
              <div class="feedback-loading-hero">
                <div class="feedback-loading-pulse"></div>
                <div>
                  <strong>Gerando revisão estruturada</strong>
                  <p>O resultado vai aparecer aqui automaticamente assim que a análise terminar.</p>
                </div>
              </div>
              <div class="feedback-loading-grid">
                <div class="feedback-skeleton-card"></div>
                <div class="feedback-skeleton-card"></div>
                <div class="feedback-skeleton-card"></div>
                <div class="feedback-skeleton-card"></div>
              </div>
            </CardContent>
          </Card>

          <Card v-else class="feedback-card feedback-card--enhanced">
            <CardHeader>
              <div class="feedback-header">
                <div>
                  <p class="eyebrow">Revisão automática</p>
                  <CardTitle>{{ submission.passed_tests }}/{{ submission.total_tests }} testes</CardTitle>
                  <CardDescription>Leitura crítica da solução com foco em qualidade, clareza e próximos ganhos.</CardDescription>
                </div>
                <div class="feedback-badges">
                  <Badge>{{ traduzirStatusExecucao(submission.status) }}</Badge>
                  <Badge variant="outline">{{ rewardSummary }}</Badge>
                </div>
              </div>
            </CardHeader>
            <CardContent class="feedback-review-layout">
              <div class="feedback-summary-hero">
                <div class="feedback-summary-hero__icon">
                  <Bot :size="18" />
                </div>
                <div class="feedback-summary-hero__copy">
                  <p class="section-label">Resumo executivo</p>
                  <strong>{{ feedbackSummary }}</strong>
                  <span>
                    {{ submission.passed_tests }}/{{ submission.total_tests }} testes concluídos · {{ rewardSummary }}
                  </span>
                </div>
              </div>

              <div v-if="hasStructuredFeedback" class="feedback-grid feedback-grid--stacked">
                <div class="feedback-column">
                  <p class="section-label">Progressão</p>
                  <p>{{ rewardSummary }}</p>
                  <ul v-if="progressRewards.length">
                    <li v-for="reward in progressRewards" :key="reward.milestone_key">{{ reward.label }}</li>
                  </ul>
                </div>
                <div class="feedback-column">
                  <p class="section-label">Resumo</p>
                  <p>{{ feedbackSummary }}</p>
                </div>
                <div class="feedback-column">
                  <p class="section-label">Pontos fortes</p>
                  <ul>
                    <li v-for="item in feedbackPayload?.strengths ?? []" :key="item">{{ item }}</li>
                  </ul>
                </div>
                <div class="feedback-column">
                  <p class="section-label">Ajustes</p>
                  <ul>
                    <li v-for="item in feedbackPayload?.issues ?? []" :key="item">{{ item }}</li>
                  </ul>
                </div>
                <div class="feedback-column feedback-column--wide">
                  <p class="section-label">Próximos passos</p>
                  <ul>
                    <li v-for="item in feedbackPayload?.next_steps ?? []" :key="item">{{ item }}</li>
                  </ul>
                </div>
              </div>

              <div v-else class="feedback-empty-state">
                <Bot :size="18" />
                <p>A revisão automática ainda não gerou uma estrutura detalhada para esta rodada.</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="chat" class="results-tab-panel">
          <div class="review-chat-log">
            <article
              v-for="(message, index) in chatMessages"
              :key="`${message.role}-${index}`"
              class="review-chat-message"
              :class="message.role"
            >
              <strong>{{ message.role === 'assistant' ? 'IA' : 'Você' }}</strong>
              <div class="markdown-body" v-html="renderMessage(message.content)"></div>
            </article>
            <div v-if="isChatBusy" class="review-chat-message assistant">
              <strong>IA</strong>
              <p><LoaderCircle class="inline-loader" :size="16" /> Revisando sua dúvida...</p>
            </div>
          </div>
          <div class="review-chat-form">
            <textarea
              v-model="chatInputModel"
              class="review-chat-input"
              rows="4"
              placeholder="Pergunte por que falhou, como melhorar a solução ou qual raciocínio a banca esperava."
            ></textarea>
            <div class="review-chat-actions">
              <Button :disabled="isChatBusy || !chatInputModel.trim()" @click="emit('send-chat')">
                <Send :size="16" />
                Enviar
              </Button>
            </div>
          </div>
        </TabsContent>
      </Tabs>
    </DialogContent>
  </Dialog>
</template>
