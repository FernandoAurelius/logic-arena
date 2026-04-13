import { computed, ref } from 'vue'

import { catalogApi } from '@/entities/catalog/api/catalog.api'
import type { ModuleSummary, NavigatorResponse, TrackSummary } from '@/entities/catalog'

type TrackStatusFilter = 'all' | 'available' | 'in_progress' | 'passed'

export function useNavigatorCatalog(authHeader: () => string | null) {
  const navigatorData = ref<NavigatorResponse | null>(null)
  const loading = ref(false)
  const errorMessage = ref('')
  const activeModule = ref<string>('all')
  const activeStatus = ref<TrackStatusFilter>('all')

  const modules = computed(() => navigatorData.value?.modules ?? [])

  function statusTone(track: TrackSummary): Exclude<TrackStatusFilter, 'all'> {
    if (track.progress_percent >= 100) return 'passed'
    if (track.progress_percent > 0) return 'in_progress'
    return 'available'
  }

  function progressLabel(track: TrackSummary) {
    if (track.progress_percent >= 100) return 'Masterizado'
    if (track.progress_percent > 0) return 'Em progresso'
    return 'Não iniciado'
  }

  function matchesStatus(track: TrackSummary) {
    if (activeStatus.value === 'all') return true
    return statusTone(track) === activeStatus.value
  }

  const visibleModules = computed<ModuleSummary[]>(() => {
    const selectedModules =
      activeModule.value === 'all'
        ? modules.value
        : modules.value.filter((module) => module.slug === activeModule.value)

    return selectedModules
      .map((module) => ({
        ...module,
        tracks: module.tracks.filter(matchesStatus),
      }))
      .filter((module) => module.tracks.length > 0)
  })

  const visibleTrackCount = computed(() =>
    visibleModules.value.reduce((total, module) => total + module.tracks.length, 0),
  )

  const recommendedTrack = computed(() => {
    const slug = navigatorData.value?.recommended_track_slug
    if (!slug) return null
    for (const module of modules.value) {
      const track = module.tracks.find((candidate) => candidate.slug === slug)
      if (track) return track
    }
    return null
  })

  const recommendedModule = computed<ModuleSummary | null>(() => {
    const slug = navigatorData.value?.recommended_module_slug
    if (!slug) return null
    return modules.value.find((module) => module.slug === slug) ?? null
  })

  async function loadNavigator() {
    loading.value = true
    errorMessage.value = ''

    try {
      navigatorData.value = await catalogApi.getNavigator(authHeader() ?? undefined)
    } catch (error) {
      console.error(error)
      errorMessage.value = 'Não foi possível carregar o Navegador agora.'
    } finally {
      loading.value = false
    }
  }

  return {
    navigatorData,
    loading,
    errorMessage,
    activeModule,
    activeStatus,
    modules,
    visibleModules,
    visibleTrackCount,
    recommendedTrack,
    recommendedModule,
    statusTone,
    progressLabel,
    loadNavigator,
  }
}
