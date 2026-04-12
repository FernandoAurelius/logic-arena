<script setup lang="ts">
import { UserRound, X } from 'lucide-vue-next'

import ThemePicker from '@/components/theme/ThemePicker.vue'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useSession } from '@/entities/session'

defineEmits<{
  close: []
}>()

const session = useSession()
</script>

<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <Card class="modal-card profile-modal-card">
      <CardHeader class="profile-modal-header">
        <div>
          <p class="eyebrow">Perfil do operador</p>
          <CardTitle>Preferências da Estação</CardTitle>
          <CardDescription>
            Ajuste tema e aparência sem sair da navegação principal.
          </CardDescription>
        </div>
        <button class="profile-modal-close" type="button" aria-label="Fechar perfil" @click="$emit('close')">
          <X :size="16" />
        </button>
      </CardHeader>
      <CardContent class="profile-modal-body">
        <div class="profile-identity">
          <div class="operator-icon operator-icon--large">
            <UserRound :size="20" />
          </div>
          <div>
            <strong>{{ session.currentUser.value?.nickname ?? 'operador' }}</strong>
            <p>Nível {{ session.currentUser.value?.level ?? 1 }} · {{ session.currentUser.value?.xp_total ?? 0 }} XP</p>
          </div>
        </div>
        <ThemePicker />
        <div class="profile-modal-actions">
          <Button class="w-full" @click="$emit('close')">Fechar</Button>
        </div>
      </CardContent>
    </Card>
  </div>
</template>
