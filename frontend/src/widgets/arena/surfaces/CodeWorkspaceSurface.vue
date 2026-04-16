<script setup lang="ts">
import { computed, watch } from 'vue'
import { FileCode2, LockKeyhole, PlaySquare, Sparkles } from 'lucide-vue-next'

import type { SessionConfig } from '@/entities/practice-session'
import { Badge } from '@/shared/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/shared/ui/card'
import MonacoEditor from '@/shared/ui/editor/MonacoEditor.vue'

const code = defineModel<string>('code', { default: '' })
const workspaceFiles = defineModel<Record<string, string>>('workspaceFiles', { default: {} })
const activeFile = defineModel<string>('activeFile', { default: '' })

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

type WorkspaceFileDescriptor = {
  path: string
  content: string
  read_only: boolean
  label: string
  role: string
}

function normalizeWorkspaceDescriptors(workspaceSpec: Record<string, unknown> | null | undefined): Record<string, WorkspaceFileDescriptor> {
  const rawFiles = workspaceSpec?.files
  if (!rawFiles || typeof rawFiles !== 'object') return {}
  return Object.fromEntries(
    Object.entries(rawFiles as Record<string, unknown>).map(([fileName, value]) => {
      if (typeof value === 'object' && value !== null) {
        const descriptor = value as Record<string, unknown>
        return [fileName, {
          path: String(descriptor.path ?? fileName),
          content: String(descriptor.content ?? ''),
          read_only: Boolean(descriptor.read_only),
          label: String(descriptor.label ?? fileName),
          role: String(descriptor.role ?? ''),
        }]
      }
      return [fileName, {
        path: fileName,
        content: String(value ?? ''),
        read_only: false,
        label: fileName,
        role: '',
      }]
    }),
  )
}

const workspaceSpec = computed(() => (props.sessionConfig?.workspace_spec ?? {}) as Record<string, unknown>)
const descriptors = computed(() => normalizeWorkspaceDescriptors(workspaceSpec.value))
const fileOrder = computed(() => {
  const explicitOrder = Array.isArray(workspaceSpec.value.file_order)
    ? workspaceSpec.value.file_order.map((value) => String(value))
    : []
  const existingFiles = Object.keys(descriptors.value)
  return explicitOrder.length > 0
    ? Array.from(new Set([...explicitOrder, ...existingFiles]))
    : existingFiles
})
const entrypoint = computed(() => String(workspaceSpec.value.entrypoint ?? fileOrder.value[0] ?? 'main.py'))
const workspaceKind = computed(() => String(workspaceSpec.value.workspace_kind ?? 'single_file'))
const language = computed(() => String(workspaceSpec.value.language ?? props.sessionConfig?.exercise.language ?? 'python'))

const fileEntries = computed(() =>
  fileOrder.value.map((fileName) => ({
    fileName,
    descriptor: descriptors.value[fileName] ?? {
      path: fileName,
      content: workspaceFiles.value[fileName] ?? '',
      read_only: false,
      label: fileName,
      role: '',
    },
  })),
)

const surfaceLabel = computed(() =>
  props.surfaceKey === 'code_editor_multifile'
    ? 'Workspace multi-arquivo'
    : 'Editor único',
)

const activeDescriptor = computed(() => {
  if (!activeFile.value) return null
  return descriptors.value[activeFile.value] ?? {
    path: activeFile.value,
    content: workspaceFiles.value[activeFile.value] ?? '',
    read_only: false,
    label: activeFile.value,
    role: activeFile.value === entrypoint.value ? 'entrypoint' : '',
  }
})
const activeFileReadOnly = computed(() => Boolean(props.readOnly || activeDescriptor.value?.read_only))
const readinessLabel = computed(() => {
  if (workspaceKind.value === 'multifile') return 'starter project'
  return 'arquivo único'
})

watch(
  descriptors,
  (nextDescriptors) => {
    if (Object.keys(workspaceFiles.value).length > 0) return
    workspaceFiles.value = Object.fromEntries(
      Object.entries(nextDescriptors).map(([fileName, descriptor]) => [fileName, descriptor.content]),
    )
  },
  { immediate: true },
)

watch(
  fileOrder,
  (files) => {
    if (!files.length) {
      activeFile.value = ''
      return
    }
    if (!activeFile.value || !files.includes(activeFile.value)) {
      activeFile.value = String(workspaceSpec.value.active_file ?? entrypoint.value ?? files[0])
    }
  },
  { immediate: true },
)

watch(
  activeFile,
  (fileName) => {
    if (!fileName) {
      code.value = ''
      return
    }
    code.value = workspaceFiles.value[fileName] ?? descriptors.value[fileName]?.content ?? ''
  },
  { immediate: true },
)

watch(
  code,
  (value) => {
    if (!activeFile.value) return
    if ((workspaceFiles.value[activeFile.value] ?? '') === value) return
    workspaceFiles.value = {
      ...workspaceFiles.value,
      [activeFile.value]: value,
    }
  },
)

function selectFile(fileName: string) {
  activeFile.value = fileName
}
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
              {{ props.exerciseTitle }} · {{ fileEntries.length }} arquivo(s) no projeto
            </CardDescription>
          </div>
          <div class="code-surface__rail-badges">
            <Badge>{{ readinessLabel }}</Badge>
            <Badge variant="outline">{{ language }}</Badge>
          </div>
        </CardHeader>
        <CardContent class="code-surface__files-list">
          <button
            v-for="{ fileName, descriptor } in fileEntries"
            :key="fileName"
            class="code-surface__file-pill"
            :class="{ active: fileName === activeFile }"
            type="button"
            @click="selectFile(fileName)"
          >
            <div class="code-surface__file-main">
              <FileCode2 :size="14" />
              <div>
                <strong>{{ descriptor.label }}</strong>
                <span>{{ descriptor.path }}</span>
              </div>
            </div>
            <div class="code-surface__file-badges">
              <Badge v-if="fileName === entrypoint" variant="outline">entrypoint</Badge>
              <Badge v-if="descriptor.read_only" variant="outline">protegido</Badge>
              <Badge v-if="fileName === activeFile">ativo</Badge>
            </div>
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
            {{ surfaceLabel }} com arquivos protegidos, starter project e estado persistido por sessão.
          </CardDescription>
        </div>
        <div class="code-surface__header-badges">
          <Badge>{{ props.surfaceKey }}</Badge>
          <Badge variant="outline">{{ activeFile || 'sem arquivo ativo' }}</Badge>
          <Badge v-if="activeFileReadOnly" variant="outline">
            <LockKeyhole :size="12" />
            readonly
          </Badge>
        </div>
      </CardHeader>
      <CardContent class="code-surface__editor-content">
        <div class="code-surface__editor-topbar">
          <div class="code-surface__editor-tab">
            <PlaySquare v-if="activeFile === entrypoint" :size="15" />
            <Sparkles v-else :size="15" />
            <span>{{ activeFile || 'Nenhum arquivo ativo' }}</span>
          </div>
          <p class="code-surface__editor-hint">
            {{ activeFileReadOnly ? 'Arquivo protegido: visível para contexto, sem edição.' : 'Arquivo editável: alterações entram na próxima execução.' }}
          </p>
        </div>
        <MonacoEditor
          v-model="code"
          class="code-surface__monaco"
          :language="language"
          height="calc(100vh - 20rem)"
          :read-only="activeFileReadOnly"
          :placeholder="`# ${activeFile || entrypoint}\n# escreva sua solução aqui`"
        />
      </CardContent>
    </Card>
  </div>
</template>

<style scoped>
.code-surface {
  display: grid;
  grid-template-columns: 18rem minmax(0, 1fr);
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
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  padding-bottom: 0.75rem;
}

.code-surface__rail-badges,
.code-surface__file-badges,
.code-surface__header-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.code-surface__files-list {
  display: grid;
  gap: 0.65rem;
}

.code-surface__file-pill {
  display: grid;
  gap: 0.65rem;
  padding: 0.85rem;
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

.code-surface__file-main {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
}

.code-surface__file-main strong,
.code-surface__editor-tab span {
  display: block;
}

.code-surface__file-main span {
  display: block;
  margin-top: 0.2rem;
  color: color-mix(in srgb, var(--foreground) 72%, transparent);
  font-size: 0.85rem;
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

.code-surface__editor-content {
  padding-top: 0;
  min-height: 0;
  overflow: hidden;
}

.code-surface__editor-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 0.85rem;
}

.code-surface__editor-tab {
  display: inline-flex;
  align-items: center;
  gap: 0.55rem;
  padding: 0.55rem 0.8rem;
  border-radius: 999px;
  background: color-mix(in srgb, var(--surface) 70%, black 30%);
  border: 1px solid color-mix(in srgb, var(--border) 75%, transparent);
}

.code-surface__editor-hint {
  margin: 0;
  font-size: 0.9rem;
  color: color-mix(in srgb, var(--foreground) 76%, transparent);
}

.code-surface__monaco {
  width: 100%;
  min-height: 0;
}

@media (max-width: 1120px) {
  .code-surface {
    grid-template-columns: 1fr;
  }

  .code-surface__files-header,
  .code-surface__editor-header,
  .code-surface__editor-topbar {
    flex-direction: column;
  }
}
</style>
