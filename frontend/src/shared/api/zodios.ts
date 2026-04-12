import { Zodios } from '@zodios/core'

import { authEndpoints, catalogEndpoints, exercisesEndpoints, submissionsEndpoints } from '@/shared/api/generated'

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'

const authClient = new Zodios(API_BASE_URL, authEndpoints) as any
const catalogClient = new Zodios(API_BASE_URL, catalogEndpoints) as any
const exercisesClient = new Zodios(API_BASE_URL, exercisesEndpoints) as any
const submissionsClient = new Zodios(API_BASE_URL, submissionsEndpoints) as any

export const apiClients = {
  auth: authClient,
  catalog: catalogClient,
  exercises: exercisesClient,
  submissions: submissionsClient,
}
