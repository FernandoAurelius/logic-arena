<script setup lang="ts">
import { cva } from 'class-variance-authority'
import { computed } from 'vue'

import { cn } from '@/lib/utils'

const badgeVariants = cva(
  'inline-flex items-center border-2 border-[var(--on-surface)] px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.12em]',
  {
    variants: {
      variant: {
        default: 'bg-[var(--primary-container)] text-[var(--on-surface)]',
        outline: 'bg-[var(--surface)] text-[var(--on-surface)]',
        dark: 'bg-[var(--on-surface)] text-[var(--surface)]',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  },
)

interface Props {
  variant?: 'default' | 'outline' | 'dark'
  class?: string
}
const props = defineProps<Props>()
const classes = computed(() => cn(badgeVariants({ variant: props.variant }), props.class))
</script>

<template>
  <div :class="classes">
    <slot />
  </div>
</template>
