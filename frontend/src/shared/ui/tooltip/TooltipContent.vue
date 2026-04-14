<script setup lang="ts">
import type { TooltipContentEmits, TooltipContentProps } from 'reka-ui'
import type { HTMLAttributes } from 'vue'
import { TooltipArrow, TooltipContent, TooltipPortal, useForwardPropsEmits } from 'reka-ui'

import { cn } from '@/lib/utils'

const props = withDefaults(defineProps<TooltipContentProps & { class?: HTMLAttributes['class'] }>(), {
  side: 'right',
  sideOffset: 10,
})

const emits = defineEmits<TooltipContentEmits>()
const forwarded = useForwardPropsEmits(props, emits)
</script>

<template>
  <TooltipPortal>
    <TooltipContent
      v-bind="forwarded"
      :class="cn('logic-tooltip-content', props.class)"
    >
      <slot />
      <TooltipArrow class="logic-tooltip-arrow" :width="10" :height="6" />
    </TooltipContent>
  </TooltipPortal>
</template>
