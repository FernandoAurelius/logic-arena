<script setup lang="ts">
import { onMounted } from 'vue'

import { useTheme } from '@/lib/theme'

const { initTheme } = useTheme()

onMounted(() => {
  initTheme()
})
</script>

<template>
  <RouterView />
</template>
