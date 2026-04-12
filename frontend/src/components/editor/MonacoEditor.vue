<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as monaco from 'monaco-editor'
import editorWorker from 'monaco-editor/esm/vs/editor/editor.worker?worker'
import tsWorker from 'monaco-editor/esm/vs/language/typescript/ts.worker?worker'
import jsonWorker from 'monaco-editor/esm/vs/language/json/json.worker?worker'

type MonacoWorkerFactory = {
  getWorker?: (_workerId: string, label: string) => Worker
}

const monacoEnvironment = globalThis as typeof globalThis & { MonacoEnvironment?: MonacoWorkerFactory }

monacoEnvironment.MonacoEnvironment = {
  getWorker(_, label) {
    if (label === 'typescript' || label === 'javascript') {
      return new tsWorker()
    }
    if (label === 'json') {
      return new jsonWorker()
    }
    return new editorWorker()
  },
}

interface Props {
  modelValue?: string
  language?: string
  height?: string
  readOnly?: boolean
  placeholder?: string
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: '',
  language: 'python',
  height: '30rem',
  readOnly: false,
  placeholder: '',
})

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const containerRef = ref<HTMLElement | null>(null)
const normalizedModelValue = computed(() => props.modelValue ?? '')
const showPlaceholder = computed(() => !props.readOnly && !normalizedModelValue.value.trim() && !!props.placeholder.trim())
let editor: monaco.editor.IStandaloneCodeEditor | null = null
let isSyncingFromModel = false

function ensureTypewriterTheme() {
  monaco.editor.defineTheme('typewriter', {
    base: 'vs-dark',
    inherit: true,
    rules: [
      { token: '', foreground: 'F4F1E8', background: '141513' },
      { token: 'comment', foreground: '7D8770', fontStyle: 'italic' },
      { token: 'keyword', foreground: 'E38645', fontStyle: 'bold' },
      { token: 'number', foreground: 'D7BA7D' },
      { token: 'string', foreground: 'A7C080' },
      { token: 'delimiter', foreground: 'F4F1E8' },
      { token: 'type.identifier', foreground: '7FB4CA' },
      { token: 'identifier', foreground: 'F4F1E8' },
      { token: 'operator', foreground: 'F4F1E8' },
    ],
    colors: {
      'editor.background': '#141513',
      'editor.foreground': '#F4F1E8',
      'editorLineNumber.foreground': '#6D6258',
      'editorLineNumber.activeForeground': '#FFB36A',
      'editorCursor.foreground': '#FF5C35',
      'editor.selectionBackground': '#5B413A66',
      'editor.inactiveSelectionBackground': '#5B413A44',
      'editor.lineHighlightBackground': '#1D1F1B',
      'editorIndentGuide.background1': '#2A2C28',
      'editorIndentGuide.activeBackground1': '#5B413A',
      'editorBracketMatch.background': '#FF5C3522',
      'editorBracketMatch.border': '#FF5C35',
      'editorGutter.background': '#171816',
      'editorWhitespace.foreground': '#343632',
      'editorOverviewRuler.border': '#00000000',
      'scrollbarSlider.background': '#8F706955',
      'scrollbarSlider.hoverBackground': '#8F706988',
      'scrollbarSlider.activeBackground': '#FF5C35AA',
    },
  })
}

onMounted(() => {
  if (!containerRef.value) return

  ensureTypewriterTheme()
  editor = monaco.editor.create(containerRef.value, {
    value: normalizedModelValue.value,
    language: props.language,
    theme: 'typewriter',
    automaticLayout: true,
    minimap: { enabled: false },
    fontFamily: 'JetBrains Mono, Fira Code, monospace',
    fontSize: 17,
    lineHeight: 28,
    lineNumbersMinChars: 3,
    padding: { top: 10, bottom: 14 },
    scrollBeyondLastLine: false,
    renderLineHighlight: 'all',
    smoothScrolling: true,
    tabSize: 2,
    roundedSelection: false,
    bracketPairColorization: { enabled: true },
    readOnly: props.readOnly,
    wordWrap: 'on',
    overviewRulerBorder: false,
    glyphMargin: false,
    folding: false,
    guides: {
      indentation: true,
      bracketPairs: true,
    },
  })

  editor.onDidChangeModelContent(() => {
    if (!editor || isSyncingFromModel) return
    emit('update:modelValue', editor.getValue())
  })
})

watch(
  () => normalizedModelValue.value,
  (value) => {
    if (!editor || editor.getValue() === value) return
    isSyncingFromModel = true
    editor.setValue(value)
    isSyncingFromModel = false
  },
)

watch(
  () => props.readOnly,
  (value) => {
    editor?.updateOptions({ readOnly: value })
  },
)

onBeforeUnmount(() => {
  editor?.dispose()
})
</script>

<template>
  <div class="monaco-shell" :style="{ height }">
    <div ref="containerRef" class="monaco-shell__editor"></div>
    <div v-if="showPlaceholder" class="monaco-placeholder">{{ placeholder }}</div>
  </div>
</template>

<style scoped>
.monaco-shell {
  position: relative;
}

.monaco-shell__editor {
  width: 100%;
  height: 100%;
}

.monaco-placeholder {
  position: absolute;
  top: 10px;
  left: 58px;
  pointer-events: none;
  color: rgba(125, 135, 112, 0.9);
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-size: 17px;
  line-height: 28px;
  font-style: italic;
  white-space: pre;
}
</style>
