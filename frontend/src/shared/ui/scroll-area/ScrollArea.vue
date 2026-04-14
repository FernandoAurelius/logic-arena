<script setup lang="ts">
import { ScrollAreaRoot, ScrollAreaScrollbar, ScrollAreaThumb, ScrollAreaViewport, ScrollAreaCorner } from 'reka-ui'
import { cn } from '@/lib/utils'
defineProps<{ class?: string; viewportClass?: string }>()
</script>

<template>
  <ScrollAreaRoot :class="cn('relative overflow-hidden', $props.class)">
    <ScrollAreaViewport :class="cn('h-full w-full rounded-[inherit]', viewportClass)">
      <slot />
    </ScrollAreaViewport>
    <ScrollAreaScrollbar orientation="vertical" class="flex w-2.5 touch-none select-none p-px">
      <ScrollAreaThumb class="relative flex-1 bg-[#8f7069]" />
    </ScrollAreaScrollbar>
    <ScrollAreaCorner />
  </ScrollAreaRoot>
</template>
