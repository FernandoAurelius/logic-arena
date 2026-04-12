<script setup lang="ts">
import { BookOpenText, MessageSquare, Play } from 'lucide-vue-next'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'

defineProps<{
  hasSubmission: boolean
  canReviewWithAi: boolean
  isChatBusy: boolean
  isSubmitting: boolean
  isBooting: boolean
  latestSubmissionStatus?: string
  latestSubmissionPassedTests?: number
  latestSubmissionTotalTests?: number
  submissionOutcomeTone: string
  submissionOutcomeTitle: string
  rewardSummary: string
}>()

defineEmits<{
  (event: 'toggle-hints'): void
  (event: 'open-review-chat'): void
  (event: 'open-results'): void
  (event: 'submit'): void
}>()

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
</script>

<template>
  <div class="arena-toolbar">
    <div class="arena-toolbar__left">
      <Button variant="outline" size="sm" @click="$emit('toggle-hints')">
        <BookOpenText :size="16" />
        Dicas
      </Button>
      <Button
        v-if="hasSubmission"
        variant="outline"
        size="sm"
        :disabled="!canReviewWithAi || isChatBusy"
        @click="$emit('open-review-chat')"
      >
        <MessageSquare :size="16" />
        Chat da revisão
      </Button>
    </div>
    <div v-if="hasSubmission" class="arena-toolbar__center">
      <div class="spec-outcome-banner spec-outcome-banner--toolbar" :data-tone="submissionOutcomeTone">
        <div class="spec-outcome-banner__status">
          <Badge>{{ traduzirStatusExecucao(latestSubmissionStatus) }}</Badge>
          <div class="spec-outcome-banner__copy">
            <strong>{{ submissionOutcomeTitle }}</strong>
            <span>{{ latestSubmissionPassedTests }}/{{ latestSubmissionTotalTests }} testes · {{ rewardSummary }}</span>
          </div>
        </div>
        <div class="spec-outcome-banner__actions">
          <Button variant="outline" size="sm" @click="$emit('open-results')">Abrir central</Button>
        </div>
      </div>
    </div>
    <div class="arena-toolbar__right">
      <Button size="sm" :disabled="isSubmitting || isBooting" @click="$emit('submit')">
        <Play :size="16" />
        {{ isSubmitting ? 'Executando...' : 'Executar' }}
      </Button>
    </div>
  </div>
</template>
