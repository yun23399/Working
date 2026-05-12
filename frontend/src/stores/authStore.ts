import { create } from 'zustand'
import type { User } from '../types/auth'

interface StoredSession {
  token: string | null
  user: User | null
}

interface AuthState {
  token: string | null
  user: User | null
  authError: string | null
  setSession: (token: string, user: User) => void
  setUser: (user: User | null) => void
  clearSession: () => void
  setAuthError: (message: string | null) => void
}

const sessionStorageKey = 'agentflow.auth.session'

function isStoredSession(value: unknown): value is StoredSession {
  if (typeof value !== 'object' || value === null) {
    return false
  }

  const candidate = value as Partial<StoredSession>
  const tokenValid = candidate.token === null || typeof candidate.token === 'string'
  const userValid = candidate.user === null || typeof candidate.user === 'object'
  return tokenValid && userValid
}

// 从本地存储恢复登录态，便于页面刷新后继续联调
function readStoredSession(): StoredSession {
  if (typeof window === 'undefined') {
    return { token: null, user: null }
  }

  const rawValue = window.localStorage.getItem(sessionStorageKey)
  if (!rawValue) {
    return { token: null, user: null }
  }

  try {
    const parsed = JSON.parse(rawValue) as unknown
    if (isStoredSession(parsed)) {
      return parsed
    }
  } catch {
    window.localStorage.removeItem(sessionStorageKey)
  }

  return { token: null, user: null }
}

// 将当前会话同步到本地存储
function persistSession(session: StoredSession): void {
  if (typeof window === 'undefined') {
    return
  }

  if (session.token === null) {
    window.localStorage.removeItem(sessionStorageKey)
    return
  }

  window.localStorage.setItem(sessionStorageKey, JSON.stringify(session))
}

const initialSession = readStoredSession()

export const useAuthStore = create<AuthState>((set) => ({
  token: initialSession.token,
  user: initialSession.user,
  authError: null,
  setSession: (token, user) => {
    persistSession({ token, user })
    set({ token, user, authError: null })
  },
  setUser: (user) => {
    const currentSession = readStoredSession()
    persistSession({ token: currentSession.token, user })
    set({ user })
  },
  clearSession: () => {
    persistSession({ token: null, user: null })
    set({ token: null, user: null, authError: null })
  },
  setAuthError: (message) => set({ authError: message }),
}))
