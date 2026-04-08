<script setup lang="ts">
import { cn } from '@/lib/utils'

defineProps<{ class?: string }>()
</script>

<template>
  <div :class="cn('border-2 border-[var(--on-surface)] bg-[var(--surface)] shadow-[4px_4px_0_var(--on-surface)]', $props.class)">
    <slot />
  </div>
</template>
