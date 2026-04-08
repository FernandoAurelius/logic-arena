<script setup lang="ts">
import { cn } from '@/lib/utils'
defineProps<{ class?: string }>()
</script>

<template>
  <div :class="cn('flex items-center px-6 pb-6', $props.class)">
    <slot />
  </div>
</template>
