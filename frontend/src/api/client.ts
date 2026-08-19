import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL
  ? `${import.meta.env.VITE_API_URL}/api/v1`
  : '/api/v1'

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config) => {
  try {
    const raw = localStorage.getItem('sf-auth')

    if (raw) {
      const state = JSON.parse(raw)
      const token = state?.state?.accessToken

      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
    }
  } catch {
    // Estado local inválido: requisição segue sem Authorization.
  }

  return config
})

type RefreshQueueItem = {
  resolve: (token: string) => void
  reject: (error: unknown) => void
}

let isRefreshing = false
let queue: RefreshQueueItem[] = []

function resolveQueue(token: string) {
  queue.forEach(({ resolve }) => resolve(token))
  queue = []
}

function rejectQueue(error: unknown) {
  queue.forEach(({ reject }) => reject(error))
  queue = []
}

function clearAuthAndRedirect() {
  localStorage.removeItem('sf-auth')

  if (window.location.pathname !== '/login') {
    window.location.href = '/login'
  }
}

api.interceptors.response.use(
  (response) => response,

  async (error) => {
    const original = error.config

    if (!original) {
      return Promise.reject(error)
    }

    if (
      error.response?.status !== 401 ||
      original._retry
    ) {
      return Promise.reject(error)
    }

    original._retry = true

    if (isRefreshing) {
      try {
        const token = await new Promise<string>(
          (resolve, reject) => {
            queue.push({ resolve, reject })
          },
        )

        original.headers.Authorization = `Bearer ${token}`

        return api(original)
      } catch (queueError) {
        return Promise.reject(queueError)
      }
    }

    isRefreshing = true

    try {
      const raw = localStorage.getItem('sf-auth')

      if (!raw) {
        throw new Error('Refresh token não disponível')
      }

      const persisted = JSON.parse(raw)
      const refreshToken = persisted?.state?.refreshToken

      if (!refreshToken) {
        throw new Error('Refresh token não disponível')
      }

      const { data } = await axios.post(
        `${API_BASE_URL}/auth/refresh`,
        {
          refresh_token: refreshToken,
        },
      )

      const currentRaw = localStorage.getItem('sf-auth')

      if (!currentRaw) {
        throw new Error('Estado de autenticação não disponível')
      }

      const current = JSON.parse(currentRaw)

      current.state.accessToken = data.access_token
      current.state.refreshToken = data.refresh_token

      localStorage.setItem(
        'sf-auth',
        JSON.stringify(current),
      )

      resolveQueue(data.access_token)

      original.headers.Authorization =
        `Bearer ${data.access_token}`

      return api(original)
    } catch (refreshError) {
      rejectQueue(refreshError)
      clearAuthAndRedirect()

      return Promise.reject(refreshError)
    } finally {
      isRefreshing = false
    }
  },
)