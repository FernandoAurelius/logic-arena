<script setup lang="ts">
import { cn } from '@/lib/utils'

defineProps<{ class?: string }>()
</script>

<template>
  <div :class="cn('border-2 border-[#1a1c1a] bg-[#f9f9f6] shadow-[4px_4px_0_#1a1c1a]', $props.class)">
    <slot />
  </div>
</template>
