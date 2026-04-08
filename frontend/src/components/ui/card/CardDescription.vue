<script setup lang="ts">
import { cn } from '@/lib/utils'
defineProps<{ class?: string }>()
</script>

<template>
  <p :class="cn('text-sm text-[#5b413a]', $props.class)">
    <slot />
  </p>
</template>
