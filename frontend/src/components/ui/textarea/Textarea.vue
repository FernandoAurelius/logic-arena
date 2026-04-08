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
        'flex min-h-[160px] w-full border-2 border-[#1a1c1a] bg-[#f4f4f1] px-3 py-2 text-sm text-[#1a1c1a] outline-none',
        $props.class,
      )
    "
    @input="$emit('update:modelValue', ($event.target as HTMLTextAreaElement).value)"
  />
</template>
