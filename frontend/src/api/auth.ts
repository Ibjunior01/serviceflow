import { api } from './client'
import type { AuthResponse, LoginRequest, User } from '@/types'

/** @deprecated use `LoginRequest` from '@/types' */
export type LoginPayload = LoginRequest

/** @deprecated use `User` from '@/types' */
export type MeResponse = User

export const authApi = {
  login: (data: LoginPayload) =>
    api.post<AuthResponse>('/auth/login', data),

  me: () =>
    api.get<MeResponse>('/auth/me'),

  refresh: (refresh_token: string) =>
    api.post<AuthResponse>('/auth/refresh', { refresh_token }),
}