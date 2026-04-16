<script setup lang="ts">
import { computed } from 'vue'

import HttpContractLabSurface from '@/components/arena/surfaces/HttpContractLabSurface.vue'
import { isHttpContractSurface, resolveArenaSurfaceKey } from '@/components/arena/surfaces/arenaSurfaceRegistry'

const props = defineProps<{
  surfaceKey?: string | null
  exercise?: unknown
  exerciseTitle?: string
  workspaceSpec?: unknown
  evaluationPlan?: unknown
  modelValue?: string
  readOnly?: boolean
}>()

const emit = defineEmits<{
  (event: 'update:modelValue', value: string): void
}>()

const resolvedSurfaceKey = computed(() => {
  const exerciseRecord = typeof props.exercise === 'object' && props.exercise !== null
    ? (props.exercise as Record<string, unknown>)
    : {}
  return props.surfaceKey ?? resolveArenaSurfaceKey({
    ...exerciseRecord,
    workspace_spec: props.workspaceSpec,
    evaluation_plan: props.evaluationPlan,
  })
})

const showHttpSurface = computed(() => isHttpContractSurface(resolvedSurfaceKey.value))
</script>

<template>
  <div class="arena-surface-host" :data-surface-key="resolvedSurfaceKey">
    <HttpContractLabSurface
      v-if="showHttpSurface"
      :model-value="modelValue"
      :exercise-title="exerciseTitle"
      :workspace-spec="workspaceSpec"
      :evaluation-plan="evaluationPlan"
      :read-only="readOnly"
      @update:model-value="emit('update:modelValue', $event)"
    />
    <template v-else>
      <slot />
    </template>
  </div>
</template>

<style scoped>
.arena-surface-host {
  display: grid;
}
</style>
