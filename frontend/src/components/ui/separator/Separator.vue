<script setup lang="ts">
import { cn } from '@/lib/utils'
defineProps<{ class?: string; orientation?: 'horizontal' | 'vertical' }>()
</script>

<template>
  <div
    :class="
      cn(
        orientation === 'vertical' ? 'h-full w-px' : 'h-px w-full',
        'bg-[#1a1c1a]',
        $props.class,
      )
    "
  />
</template>
