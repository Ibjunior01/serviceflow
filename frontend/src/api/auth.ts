import { api } from './client'

export interface LoginPayload {
  email: string
  password: string
}

export interface AuthResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface MeResponse {
  id: string
  full_name: string
  email: string
  role: 'owner' | 'admin' | 'technician' | 'viewer'
  company_id: string
}

export const authApi = {
  login: (data: LoginPayload) =>
    api.post<AuthResponse>('/auth/login', data),

  me: () =>
    api.get<MeResponse>('/auth/me'),

  refresh: (refresh_token: string) =>
    api.post<AuthResponse>('/auth/refresh', { refresh_token }),
}