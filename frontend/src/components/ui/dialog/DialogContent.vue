<script setup lang="ts">
import type { DialogContentEmits, DialogContentProps } from 'reka-ui'
import type { HTMLAttributes } from 'vue'
import { DialogClose, DialogContent, DialogOverlay, DialogPortal, useForwardPropsEmits } from 'reka-ui'
import { X } from 'lucide-vue-next'

import { cn } from '@/lib/utils'

const props = withDefaults(defineProps<DialogContentProps & { class?: HTMLAttributes['class']; showClose?: boolean }>(), {
  showClose: true,
})
const emits = defineEmits<DialogContentEmits>()
const forwarded = useForwardPropsEmits(props, emits)
</script>

<template>
  <DialogPortal>
    <DialogOverlay class="dialog-overlay" />
    <DialogContent
      v-bind="forwarded"
      :class="cn('dialog-content', props.class)"
    >
      <slot />
      <DialogClose v-if="showClose" class="dialog-close">
        <X :size="16" />
      </DialogClose>
    </DialogContent>
  </DialogPortal>
</template>
