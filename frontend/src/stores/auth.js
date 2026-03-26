import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

const AUTH_TOKEN_KEY = 'auth_token'
const AUTH_REFRESH_TOKEN_KEY = 'auth_refresh_token'
const AUTH_USER_KEY = 'auth_user'
const AUTH_REMEMBER_KEY = 'auth_remember'
const AUTH_REMEMBER_USERNAME_KEY = 'auth_remember_username'
const AUTH_SAVED_USERNAME_KEY = 'auth_saved_username'
const LEGACY_TOKEN_KEY = 'token'
const LEGACY_USER_KEY = 'user'

function parseUser(rawValue) {
  if (!rawValue) return null
  try {
    return JSON.parse(rawValue)
  } catch {
    return null
  }
}

function clearAuthStorage(storage) {
  storage.removeItem(AUTH_TOKEN_KEY)
  storage.removeItem(AUTH_REFRESH_TOKEN_KEY)
  storage.removeItem(AUTH_USER_KEY)
  storage.removeItem(LEGACY_TOKEN_KEY)
  storage.removeItem(LEGACY_USER_KEY)
}

function getStoredUsername() {
  return window.localStorage.getItem(AUTH_SAVED_USERNAME_KEY) || ''
}

function getInitialAuthState() {
  const persistentToken = window.localStorage.getItem(AUTH_TOKEN_KEY) || window.localStorage.getItem(LEGACY_TOKEN_KEY) || ''
  const persistentRefreshToken = window.localStorage.getItem(AUTH_REFRESH_TOKEN_KEY) || ''
  const persistentUser = parseUser(window.localStorage.getItem(AUTH_USER_KEY) || window.localStorage.getItem(LEGACY_USER_KEY))
  if (persistentToken) {
    return {
      token: persistentToken,
      refreshToken: persistentRefreshToken,
      user: persistentUser,
      rememberMe: true,
    }
  }

  return {
    token: window.sessionStorage.getItem(AUTH_TOKEN_KEY) || '',
    refreshToken: window.sessionStorage.getItem(AUTH_REFRESH_TOKEN_KEY) || '',
    user: parseUser(window.sessionStorage.getItem(AUTH_USER_KEY)),
    rememberMe: false,
  }
}

function normalizeAuthPayload(authPayload, currentRefreshToken = '') {
  return {
    accessToken: authPayload?.access_token || authPayload?.accessToken || '',
    refreshToken: authPayload?.refresh_token || authPayload?.refreshToken || currentRefreshToken || '',
    user: authPayload?.user || null,
  }
}

export const useAuthStore = defineStore('auth', () => {
  const initialState = getInitialAuthState()
  const token = ref(initialState.token)
  const refreshToken = ref(initialState.refreshToken)
  const user = ref(initialState.user)
  const rememberMe = ref(window.localStorage.getItem(AUTH_REMEMBER_KEY) === '1' || initialState.rememberMe)
  const rememberUsername = ref(window.localStorage.getItem(AUTH_REMEMBER_USERNAME_KEY) === '1' || Boolean(getStoredUsername()))
  const rememberedUsername = ref(getStoredUsername())

  const isAdmin = computed(() => user.value?.role === 'admin')

  function persistAuth(accessToken, nextRefreshToken, userValue, shouldRemember) {
    clearAuthStorage(window.localStorage)
    clearAuthStorage(window.sessionStorage)

    const storage = shouldRemember ? window.localStorage : window.sessionStorage
    storage.setItem(AUTH_TOKEN_KEY, accessToken)
    storage.setItem(AUTH_REFRESH_TOKEN_KEY, nextRefreshToken)
    storage.setItem(AUTH_USER_KEY, JSON.stringify(userValue))

    if (shouldRemember) {
      window.localStorage.setItem(AUTH_REMEMBER_KEY, '1')
    } else {
      window.localStorage.removeItem(AUTH_REMEMBER_KEY)
    }
  }

  function persistRememberedUsername(usernameValue = '') {
    const normalizedUsername = usernameValue.trim()
    rememberedUsername.value = normalizedUsername
    if (rememberUsername.value && normalizedUsername) {
      window.localStorage.setItem(AUTH_SAVED_USERNAME_KEY, normalizedUsername)
      window.localStorage.setItem(AUTH_REMEMBER_USERNAME_KEY, '1')
      return
    }
    window.localStorage.removeItem(AUTH_SAVED_USERNAME_KEY)
    if (!rememberUsername.value) {
      window.localStorage.removeItem(AUTH_REMEMBER_USERNAME_KEY)
    }
  }

  function setRememberPreference(value) {
    rememberMe.value = Boolean(value)
    if (rememberMe.value) {
      window.localStorage.setItem(AUTH_REMEMBER_KEY, '1')
    } else {
      window.localStorage.removeItem(AUTH_REMEMBER_KEY)
    }
  }

  function setRememberUsernamePreference(value, usernameValue = rememberedUsername.value) {
    rememberUsername.value = Boolean(value)
    if (!rememberUsername.value) {
      rememberedUsername.value = ''
      window.localStorage.removeItem(AUTH_REMEMBER_USERNAME_KEY)
      window.localStorage.removeItem(AUTH_SAVED_USERNAME_KEY)
      return
    }
    window.localStorage.setItem(AUTH_REMEMBER_USERNAME_KEY, '1')
    persistRememberedUsername(usernameValue)
  }

  function setAuth(authPayload, options = {}) {
    const normalized = normalizeAuthPayload(authPayload, refreshToken.value)
    const shouldRemember = options.rememberMe ?? rememberMe.value
    const shouldRememberUsername = options.rememberUsername ?? rememberUsername.value
    const usernameValue = options.username ?? normalized.user?.username ?? rememberedUsername.value

    token.value = normalized.accessToken
    refreshToken.value = normalized.refreshToken
    user.value = normalized.user
    rememberMe.value = Boolean(shouldRemember)
    rememberUsername.value = Boolean(shouldRememberUsername)

    persistAuth(normalized.accessToken, normalized.refreshToken, normalized.user, rememberMe.value)

    if (rememberUsername.value) {
      persistRememberedUsername(usernameValue)
    } else {
      rememberedUsername.value = ''
      window.localStorage.removeItem(AUTH_REMEMBER_USERNAME_KEY)
      window.localStorage.removeItem(AUTH_SAVED_USERNAME_KEY)
    }
  }

  function updateAccessSession(authPayload) {
    setAuth(authPayload, {
      rememberMe: rememberMe.value,
      rememberUsername: rememberUsername.value,
      username: rememberedUsername.value || user.value?.username || '',
    })
  }

  function logout() {
    token.value = ''
    refreshToken.value = ''
    user.value = null
    clearAuthStorage(window.localStorage)
    clearAuthStorage(window.sessionStorage)
  }

  return {
    token,
    refreshToken,
    user,
    rememberMe,
    rememberUsername,
    rememberedUsername,
    isAdmin,
    setAuth,
    updateAccessSession,
    setRememberPreference,
    setRememberUsernamePreference,
    logout,
  }
})
