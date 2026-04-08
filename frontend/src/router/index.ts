import { createRouter, createWebHistory } from 'vue-router'

import LandingView from '@/views/LandingView.vue'
import ArenaView from '@/views/ArenaView.vue'
import { useSession } from '@/lib/session'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'landing',
      component: LandingView,
    },
    {
      path: '/arena',
      name: 'arena',
      component: ArenaView,
      meta: { requiresAuth: true },
    },
  ],
})

router.beforeEach(async (to) => {
  const session = useSession()
  await session.initSession()

  if (to.meta.requiresAuth && !session.isAuthenticated.value) {
    return { name: 'landing' }
  }

  return true
})

export default router
