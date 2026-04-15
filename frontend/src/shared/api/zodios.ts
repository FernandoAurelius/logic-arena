import { Zodios } from '@zodios/core'

import { assessmentsEndpoints, authEndpoints, catalogEndpoints, practiceEndpoints, reviewEndpoints } from '@/shared/api/generated'

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'

const authClient = new Zodios(API_BASE_URL, authEndpoints) as any
const catalogClient = new Zodios(API_BASE_URL, catalogEndpoints) as any
const practiceClient = new Zodios(API_BASE_URL, practiceEndpoints) as any
const assessmentsClient = new Zodios(API_BASE_URL, assessmentsEndpoints) as any
const reviewClient = new Zodios(API_BASE_URL, reviewEndpoints) as any

export const apiClients = {
  auth: authClient,
  catalog: catalogClient,
  practice: practiceClient,
  assessments: assessmentsClient,
  review: reviewClient,
}
