<script setup lang="ts">
import type { DialogTriggerProps } from 'reka-ui'
import type { HTMLAttributes } from 'vue'
import { DialogTrigger } from 'reka-ui'

import { cn } from '@/lib/utils'

const props = defineProps<DialogTriggerProps & { class?: HTMLAttributes['class'] }>()
</script>

<template>
  <DialogTrigger :class="cn(props.class)">
    <slot />
  </DialogTrigger>
</template>
