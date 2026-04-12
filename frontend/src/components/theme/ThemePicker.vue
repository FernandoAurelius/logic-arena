<script setup lang="ts">
import { useTheme } from '@/lib/theme'

const theme = useTheme()
</script>

<template>
  <section
    class="grid gap-3 rounded border border-[var(--on-surface)] bg-[var(--surface)] p-3 shadow-[4px_4px_0_var(--on-surface)]"
    aria-label="Theme picker"
  >
    <div class="flex items-center justify-between gap-3">
      <div class="grid gap-0.5">
        <p class="text-[0.7rem] uppercase tracking-[0.18em] text-[var(--primary)]">Theme</p>
        <strong class="text-sm uppercase tracking-[0.06em]">Appearance</strong>
      </div>
      <span class="text-[0.68rem] uppercase tracking-[0.16em] text-[var(--on-surface-variant)]">
        {{ theme.activeAccent.value }}
      </span>
    </div>

    <div class="grid gap-2">
      <p class="text-[0.7rem] uppercase tracking-[0.18em] text-[var(--on-surface-variant)]">Modo</p>
      <div class="flex flex-wrap gap-2">
        <button
          v-for="mode in theme.modeOptions.value"
          :key="mode.id"
          type="button"
          class="rounded border border-[var(--on-surface)] px-3 py-2 text-xs font-semibold uppercase tracking-[0.12em] transition-transform active:translate-x-[1px] active:translate-y-[1px]"
          :class="theme.theme.value === mode.id ? 'bg-[var(--primary)] text-[var(--on-primary)]' : 'bg-[var(--surface-container)] text-[var(--on-surface)]'"
          :aria-pressed="theme.theme.value === mode.id"
          @click="theme.setThemeMode(mode.id)"
        >
          {{ mode.label }}
        </button>
      </div>
    </div>

    <div class="grid gap-2">
      <p class="text-[0.7rem] uppercase tracking-[0.18em] text-[var(--on-surface-variant)]">Accent</p>
      <div class="flex flex-wrap gap-2">
        <button
          v-for="accent in theme.accentOptions.value"
          :key="accent.id"
          type="button"
          class="rounded border border-[var(--on-surface)] px-3 py-2 text-xs font-semibold uppercase tracking-[0.12em] transition-transform active:translate-x-[1px] active:translate-y-[1px]"
          :class="theme.activeAccent.value === accent.id ? 'bg-[var(--primary)] text-[var(--on-primary)]' : 'bg-[var(--surface-container)] text-[var(--on-surface)]'"
          :aria-pressed="theme.activeAccent.value === accent.id"
          :title="accent.description"
          @click="theme.setAccent(accent.id)"
        >
          {{ accent.label }}
        </button>
      </div>
    </div>
  </section>
</template>
