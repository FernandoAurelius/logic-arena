<script setup lang="ts">
import { cn } from '@/lib/utils'
defineProps<{ class?: string; modelValue?: string; type?: string; placeholder?: string; disabled?: boolean }>()
defineEmits<{ 'update:modelValue': [value: string] }>()
</script>

<template>
  <input
    :type="type ?? 'text'"
    :value="modelValue"
    :placeholder="placeholder"
    :disabled="disabled"
    :class="
      cn(
        'flex h-11 w-full border-2 border-[var(--on-surface)] bg-[var(--surface-low)] px-3 py-2 text-sm text-[var(--on-surface)] outline-none placeholder:text-[var(--on-surface-variant)]',
        $props.class,
      )
    "
    @input="$emit('update:modelValue', ($event.target as HTMLInputElement).value)"
  />
</template>
