import { createRouter, createWebHistory } from 'vue-router'

import LandingPage from '@/pages/landing/ui/LandingPage.vue'
import NavigatorPage from '@/pages/navigator/ui/NavigatorPage.vue'
import TrackPage from '@/pages/track/ui/TrackPage.vue'
import ExplanationPage from '@/pages/explanation/ui/ExplanationPage.vue'
import TutorialPage from '@/pages/tutorial/ui/TutorialPage.vue'
import ProfilePage from '@/pages/profile/ui/ProfilePage.vue'
import ArenaPage from '@/pages/arena/ui/ArenaPage.vue'
import { useSession } from '@/entities/session'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'landing',
      component: LandingPage,
    },
    {
      path: '/navigator',
      name: 'navigator',
      component: NavigatorPage,
      meta: { requiresAuth: true },
    },
    {
      path: '/tracks/:trackSlug',
      name: 'track',
      component: TrackPage,
      meta: { requiresAuth: true },
    },
    {
      path: '/tracks/:trackSlug/explanation/:exerciseSlug',
      name: 'track-explanation',
      component: ExplanationPage,
      meta: { requiresAuth: true },
    },
    {
      path: '/profile',
      name: 'profile',
      component: ProfilePage,
      meta: { requiresAuth: true },
    },
    {
      path: '/arena',
      name: 'arena',
      component: ArenaPage,
      meta: { requiresAuth: true },
    },
    {
      path: '/ajuda',
      name: 'tutorial',
      component: TutorialPage,
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
