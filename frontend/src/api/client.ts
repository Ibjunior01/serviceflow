import axios from 'axios'

export const api = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config) => {
  try {
    const raw = localStorage.getItem('sf-auth')
    if (raw) {
      const state = JSON.parse(raw)
      const token = state?.state?.accessToken
      if (token) config.headers.Authorization = `Bearer ${token}`
    }
  } catch {}
  return config
})

let isRefreshing = false
let queue: Array<(token: string) => void> = []

api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config

    if (error.response?.status === 401 && !original._retry) {
      original._retry = true

      if (isRefreshing) {
        return new Promise((resolve) => {
          queue.push((token) => {
            original.headers.Authorization = `Bearer ${token}`
            resolve(api(original))
          })
        })
      }

      isRefreshing = true
      try {
        const raw = localStorage.getItem('sf-auth')
        if (!raw) throw new Error('no token')
        const state = JSON.parse(raw)
        const refreshToken = state?.state?.refreshToken
        if (!refreshToken) throw new Error('no refresh token')

        const { data } = await axios.post('/api/v1/auth/refresh', {
          refresh_token: refreshToken,
        })

        const current = JSON.parse(localStorage.getItem('sf-auth') || '{}')
        current.state.accessToken = data.access_token
        current.state.refreshToken = data.refresh_token
        localStorage.setItem('sf-auth', JSON.stringify(current))

        queue.forEach((cb) => cb(data.access_token))
        queue = []
        original.headers.Authorization = `Bearer ${data.access_token}`
        return api(original)
      } catch {
        localStorage.removeItem('sf-auth')
        window.location.href = '/login'
      } finally {
        isRefreshing = false
      }
    }

    return Promise.reject(error)
  }
)