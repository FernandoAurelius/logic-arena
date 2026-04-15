<script setup lang="ts">
import { computed, ref, watch } from 'vue'

import type { SessionConfig } from '@/entities/practice-session'
import { Badge } from '@/shared/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/shared/ui/card'
import MonacoEditor from '@/shared/ui/editor/MonacoEditor.vue'

const code = defineModel<string>('code', { default: '' })

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

const activeFile = ref('main.py')

function toWorkspaceFiles(workspaceSpec: Record<string, unknown> | null | undefined) {
  if (!workspaceSpec || typeof workspaceSpec !== 'object') return []
  const candidateKeys = ['files', 'file_names', 'workspace_files', 'editor_files', 'project_files']
  for (const key of candidateKeys) {
    const value = (workspaceSpec as Record<string, unknown>)[key]
    if (Array.isArray(value)) {
      return value.map((item) => String(item))
    }
  }
  return []
}

const workspaceFiles = computed(() => {
  const files = toWorkspaceFiles(props.sessionConfig?.workspace_spec as Record<string, unknown> | null | undefined)
  if (files.length > 0) return files
  if (props.surfaceKey === 'code_editor_multifile') return ['main.py', 'helpers.py', 'tests.py']
  return ['main.py']
})

const surfaceLabel = computed(() =>
  props.surfaceKey === 'code_editor_multifile'
    ? 'Workspace multi-arquivo'
    : 'Editor único',
)

watch(
  workspaceFiles,
  (files) => {
    if (!files.includes(activeFile.value)) {
      activeFile.value = files[0] ?? 'main.py'
    }
  },
  { immediate: true },
)
</script>

<template>
  <div class="code-surface">
    <div class="code-surface__rail">
      <Card class="code-surface__files">
        <CardHeader class="code-surface__files-header">
          <div>
            <p class="eyebrow">Arquivos</p>
            <CardTitle>{{ surfaceLabel }}</CardTitle>
            <CardDescription>
              {{ props.exerciseTitle }} · {{ workspaceFiles.length }} arquivo(s) visível(eis)
            </CardDescription>
          </div>
        </CardHeader>
        <CardContent class="code-surface__files-list">
          <button
            v-for="file in workspaceFiles"
            :key="file"
            class="code-surface__file-pill"
            :class="{ active: file === activeFile }"
            type="button"
            @click="activeFile = file"
          >
            <span>{{ file }}</span>
            <Badge variant="outline">{{ file === activeFile ? 'ativo' : 'visível' }}</Badge>
          </button>
        </CardContent>
      </Card>
    </div>

    <Card class="code-surface__editor">
      <CardHeader class="code-surface__editor-header">
        <div>
          <p class="eyebrow">Superfície principal</p>
          <CardTitle>{{ props.exerciseTitle }}</CardTitle>
          <CardDescription>
            {{ surfaceLabel }} pronto para executar, verificar e submeter sem depender do fluxo legado.
          </CardDescription>
        </div>
        <div class="code-surface__header-badges">
          <Badge>{{ props.surfaceKey }}</Badge>
          <Badge variant="outline">{{ props.readOnly ? 'somente leitura' : 'editável' }}</Badge>
        </div>
      </CardHeader>
      <CardContent class="code-surface__editor-content">
        <MonacoEditor
          v-model="code"
          class="code-surface__monaco"
          language="python"
          height="calc(100vh - 17.5rem)"
          :read-only="props.readOnly"
          :placeholder="`# ${activeFile}\n# escreva sua solução aqui`"
        />
      </CardContent>
    </Card>
  </div>
</template>

<style scoped>
.code-surface {
  display: grid;
  grid-template-columns: 15rem minmax(0, 1fr);
  gap: 1rem;
  min-height: 0;
  height: 100%;
}

.code-surface__rail,
.code-surface__editor,
.code-surface__files {
  min-height: 0;
}

.code-surface__rail {
  display: flex;
  flex-direction: column;
}

.code-surface__files {
  height: 100%;
}

.code-surface__files-header {
  padding-bottom: 0.75rem;
}

.code-surface__files-list {
  display: grid;
  gap: 0.65rem;
}

.code-surface__file-pill {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0.75rem 0.85rem;
  border: 1.5px solid color-mix(in srgb, var(--border) 90%, transparent);
  background: color-mix(in srgb, var(--surface) 92%, var(--primary) 8%);
  border-radius: 0.95rem;
  text-align: left;
  transition:
    transform 180ms ease,
    border-color 180ms ease,
    background 180ms ease,
    box-shadow 180ms ease;
}

.code-surface__file-pill.active {
  border-color: var(--primary);
  background: color-mix(in srgb, var(--primary-container) 28%, var(--surface));
  box-shadow: 0 0 0 1px color-mix(in srgb, var(--primary) 35%, transparent);
}

.code-surface__file-pill:hover {
  transform: translateY(-1px);
}

.code-surface__editor {
  display: grid;
  grid-template-rows: auto 1fr;
  overflow: hidden;
}

.code-surface__editor-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}

.code-surface__header-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  justify-content: flex-end;
}

.code-surface__editor-content {
  padding-top: 0;
  min-height: 0;
  overflow: hidden;
}

.code-surface__monaco {
  width: 100%;
  min-height: 0;
}

@media (max-width: 1120px) {
  .code-surface {
    grid-template-columns: 1fr;
  }
}
</style>
