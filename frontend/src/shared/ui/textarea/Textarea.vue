<script setup lang="ts">
import { cn } from '@/lib/utils'
defineProps<{ class?: string; modelValue?: string; placeholder?: string; disabled?: boolean; spellcheck?: boolean }>()
defineEmits<{ 'update:modelValue': [value: string] }>()
</script>

<template>
  <textarea
    :value="modelValue"
    :placeholder="placeholder"
    :disabled="disabled"
    :spellcheck="spellcheck"
    :class="
      cn(
        'flex min-h-[160px] w-full border-2 border-[var(--on-surface)] bg-[var(--surface-low)] px-3 py-2 text-sm text-[var(--on-surface)] outline-none placeholder:text-[var(--on-surface-variant)]',
        $props.class,
      )
    "
    @input="$emit('update:modelValue', ($event.target as HTMLTextAreaElement).value)"
  />
</template>
