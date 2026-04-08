<script setup lang="ts">
import { cva } from 'class-variance-authority'
import { computed } from 'vue'

import { cn } from '@/lib/utils'

const badgeVariants = cva(
  'inline-flex items-center border-2 border-[#1a1c1a] px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.12em]',
  {
    variants: {
      variant: {
        default: 'bg-[#ff5c35] text-[#1a1c1a]',
        outline: 'bg-[#f9f9f6] text-[#1a1c1a]',
        dark: 'bg-[#1a1c1a] text-[#f9f9f6]',
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
