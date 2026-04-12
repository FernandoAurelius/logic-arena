import { createRouter, createWebHistory } from 'vue-router'

import LandingView from '@/views/LandingView.vue'
import ArenaView from '@/views/ArenaView.vue'
import NavigatorView from '@/views/NavigatorView.vue'
import TrackView from '@/views/TrackView.vue'
import ExplanationView from '@/views/ExplanationView.vue'
import TutorialView from '@/views/TutorialView.vue'
import { useSession } from '@/entities/session'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'landing',
      component: LandingView,
    },
    {
      path: '/navigator',
      name: 'navigator',
      component: NavigatorView,
      meta: { requiresAuth: true },
    },
    {
      path: '/tracks/:trackSlug',
      name: 'track',
      component: TrackView,
      meta: { requiresAuth: true },
    },
    {
      path: '/tracks/:trackSlug/explanation/:exerciseSlug',
      name: 'track-explanation',
      component: ExplanationView,
      meta: { requiresAuth: true },
    },
    {
      path: '/profile',
      redirect: { name: 'navigator' },
    },
    {
      path: '/arena',
      name: 'arena',
      component: ArenaView,
      meta: { requiresAuth: true },
    },
    {
      path: '/ajuda',
      name: 'tutorial',
      component: TutorialView,
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
