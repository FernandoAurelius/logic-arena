<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

import { useSession } from '@/entities/session'
import { Button } from '@/shared/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/shared/ui/card'
import { Input } from '@/shared/ui/input'

const emit = defineEmits<{
  close: []
}>()

const router = useRouter()
const session = useSession()
const nickname = ref('')
const password = ref('')
const errorMessage = ref('')

async function handleLogin() {
  errorMessage.value = ''

  try {
    await session.login(nickname.value, password.value)
    emit('close')
    await router.push({ name: 'navigator' })
  } catch (error) {
    console.error(error)
    errorMessage.value = 'Não foi possível autenticar com esse nickname e senha.'
  }
}
</script>

<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <Card class="modal-card">
      <CardHeader>
        <p class="eyebrow">Access Node</p>
        <CardTitle>Entrar na Arena</CardTitle>
        <CardDescription>
          Use um nickname interno. Se ainda não existir, a conta é criada automaticamente no primeiro acesso.
        </CardDescription>
      </CardHeader>
      <CardContent class="modal-content">
        <div class="field-stack">
          <label class="field-label" for="modal-nickname">Nickname</label>
          <Input id="modal-nickname" v-model="nickname" placeholder="miguel" />
        </div>
        <div class="field-stack">
          <label class="field-label" for="modal-password">Senha</label>
          <Input id="modal-password" v-model="password" type="password" placeholder="••••••••" />
        </div>
        <div class="auth-actions">
          <Button :disabled="session.authBusy.value || !nickname || !password" @click="handleLogin">
            {{ session.authBusy.value ? 'SYNCING...' : 'ENTRAR' }}
          </Button>
          <Button variant="outline" @click="$emit('close')">Cancelar</Button>
        </div>
        <p v-if="errorMessage" class="notice error">{{ errorMessage }}</p>
      </CardContent>
    </Card>
  </div>
</template>
