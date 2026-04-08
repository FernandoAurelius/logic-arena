import { Zodios } from '@zodios/core'

import { authEndpoints, exercisesEndpoints, submissionsEndpoints } from './generated'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'

export const authApi = new Zodios(API_BASE_URL, authEndpoints)
export const exercisesApi = new Zodios(API_BASE_URL, exercisesEndpoints)
export const submissionsApi = new Zodios(API_BASE_URL, submissionsEndpoints)
