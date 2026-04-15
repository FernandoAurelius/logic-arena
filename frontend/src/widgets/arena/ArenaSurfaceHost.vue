<script setup lang="ts">
import { computed } from 'vue'

import type { SessionConfig } from '@/entities/practice-session'
import { Badge } from '@/shared/ui/badge'
import { Card, CardContent, CardHeader, CardDescription, CardTitle } from '@/shared/ui/card'

import CodeWorkspaceSurface from './surfaces/CodeWorkspaceSurface.vue'
import ObjectiveChoicesSurface from './surfaces/ObjectiveChoicesSurface.vue'
import ObjectiveClassifierSurface from './surfaces/ObjectiveClassifierSurface.vue'
import { getArenaSurfaceDescriptor } from './surfaces/arenaSurfaceRegistry'
import SurfacePlaceholder from './surfaces/SurfacePlaceholder.vue'

const code = defineModel<string>('code', { default: '' })
const selectedOptions = defineModel<string[]>('selectedOptions', { default: [] })
const responseText = defineModel<string>('responseText', { default: '' })

const props = withDefaults(defineProps<{
  surfaceKey?: string | null
  readOnly?: boolean
  exerciseTitle?: string
  sessionConfig?: SessionConfig | null
}>(), {
  surfaceKey: 'code_editor_single',
  readOnly: false,
  exerciseTitle: 'atividade',
  sessionConfig: null,
})

const surface = computed(() => getArenaSurfaceDescriptor(props.surfaceKey))
</script>

<template>
  <Card class="surface-host">
    <CardHeader class="surface-host__header">
      <div>
        <p class="eyebrow">Superfície canônica</p>
        <CardTitle>{{ surface.title }}</CardTitle>
        <CardDescription>{{ surface.description }}</CardDescription>
      </div>
      <div class="surface-host__badges">
        <Badge>{{ surface.key }}</Badge>
        <Badge variant="outline">{{ surface.kind }}</Badge>
        <Badge variant="outline">{{ props.sessionConfig?.family_key ?? 'family_key' }}</Badge>
        <Badge variant="outline">{{ props.sessionConfig?.mode ?? 'practice' }}</Badge>
      </div>
    </CardHeader>
    <CardContent class="surface-host__content">
      <CodeWorkspaceSurface
        v-if="surface.kind === 'code'"
        v-model="code"
        :surface-key="surface.key"
        :read-only="props.readOnly"
        :exercise-title="props.exerciseTitle"
        :session-config="props.sessionConfig"
      />
      <ObjectiveChoicesSurface
        v-else-if="surface.key === 'objective_choices'"
        v-model:selected-options="selectedOptions"
        v-model:response-text="responseText"
        :read-only="props.readOnly"
        :exercise-title="props.exerciseTitle"
        :session-config="props.sessionConfig"
      />
      <ObjectiveClassifierSurface
        v-else-if="surface.key === 'objective_classifier'"
        v-model:selected-options="selectedOptions"
        v-model:response-text="responseText"
        :read-only="props.readOnly"
        :exercise-title="props.exerciseTitle"
        :session-config="props.sessionConfig"
      />
      <SurfacePlaceholder
        v-else
        :surface="surface"
        :exercise-title="props.exerciseTitle"
        :session-config="props.sessionConfig"
      />
    </CardContent>
  </Card>
</template>

<style scoped>
.surface-host {
  display: grid;
  grid-template-rows: auto 1fr;
  min-height: 0;
  height: 100%;
}

.surface-host__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}

.surface-host__badges {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 0.5rem;
}

.surface-host__content {
  min-height: 0;
  overflow: hidden;
  padding-top: 0;
}
</style>
