import { Zodios } from '@zodios/core'

import { authEndpoints, exercisesEndpoints, submissionsEndpoints } from './generated'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'

// The OpenAPI contract remains the source of truth; we relax the consumer surface
// here because the generated file groups endpoints but doesn't emit a stable typed
// helper for path-based methods in this version of openapi-zod-client.
export const authApi = new Zodios(API_BASE_URL, authEndpoints) as any
export const exercisesApi = new Zodios(API_BASE_URL, exercisesEndpoints) as any
export const submissionsApi = new Zodios(API_BASE_URL, submissionsEndpoints) as any
