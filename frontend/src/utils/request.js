import axios from 'axios'
import router from '../router'
import { useAuthStore } from '../stores/auth'

const request = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

const refreshClient = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

let refreshPromise = null

async function refreshAccessToken(auth) {
  if (!auth.refreshToken) {
    throw new Error('missing refresh token')
  }

  if (!refreshPromise) {
    refreshPromise = refreshClient
      .post('/auth/refresh', { refresh_token: auth.refreshToken })
      .then((res) => res.data)
      .finally(() => {
        refreshPromise = null
      })
  }

  const payload = await refreshPromise
  auth.updateAccessSession(payload)
  return payload.access_token
}

function shouldAttemptRefresh(error) {
  const status = error.response?.status
  const originalRequest = error.config || {}
  const requestUrl = String(originalRequest.url || '')
  if (status !== 401) return false
  if (originalRequest._retry) return false
  if (originalRequest.skipAuthRefresh) return false
  if (requestUrl.includes('/auth/login')) return false
  if (requestUrl.includes('/auth/refresh')) return false
  return true
}

request.interceptors.request.use((config) => {
  const auth = useAuthStore()
  if (auth.token) {
    config.headers.Authorization = `Bearer ${auth.token}`
  }
  return config
})

request.interceptors.response.use(
  (res) => res.data,
  async (err) => {
    const auth = useAuthStore()
    const originalRequest = err.config || {}

    if (shouldAttemptRefresh(err) && auth.refreshToken) {
      originalRequest._retry = true
      try {
        const nextAccessToken = await refreshAccessToken(auth)
        originalRequest.headers = originalRequest.headers || {}
        originalRequest.headers.Authorization = `Bearer ${nextAccessToken}`
        return request(originalRequest)
      } catch (refreshError) {
        auth.logout()
        if (router.currentRoute.value.path !== '/login') {
          router.push('/login')
        }
        return Promise.reject(refreshError)
      }
    }

    if (err.response?.status === 401) {
      auth.logout()
      if (router.currentRoute.value.path !== '/login') {
        router.push('/login')
      }
    }
    return Promise.reject(err)
  }
)

export default request
