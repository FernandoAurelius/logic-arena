<script setup lang="ts">
import { cva } from 'class-variance-authority'
import { computed } from 'vue'

import { cn } from '@/lib/utils'

const buttonVariants = cva(
  'inline-flex items-center justify-center gap-2 whitespace-nowrap text-sm font-bold uppercase tracking-[0.08em] transition-all disabled:pointer-events-none disabled:opacity-50',
  {
    variants: {
      variant: {
        default: 'border-2 border-[var(--on-surface)] bg-[var(--primary)] text-[var(--on-primary)] shadow-[4px_4px_0_var(--on-surface)]',
        outline: 'border-2 border-[var(--on-surface)] bg-[var(--surface)] text-[var(--on-surface)]',
        ghost: 'border-2 border-[var(--on-surface)] bg-transparent text-[var(--on-surface)]',
      },
      size: {
        default: 'px-4 py-3',
        sm: 'px-3 py-2 text-xs',
        lg: 'px-5 py-4',
        icon: 'h-10 w-10',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  },
)

interface Props {
  variant?: 'default' | 'outline' | 'ghost'
  size?: 'default' | 'sm' | 'lg' | 'icon'
  class?: string
  type?: 'button' | 'submit' | 'reset'
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  type: 'button',
})

const classes = computed(() => cn(buttonVariants({ variant: props.variant, size: props.size }), props.class))
</script>

<template>
  <button :type="type" :disabled="disabled" :class="classes">
    <slot />
  </button>
</template>
