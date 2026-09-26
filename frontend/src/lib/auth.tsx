/** Estado de sesión compartido por toda la app. */

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import { api, getToken, onUnauthorized, setToken } from './api'
import type { TokenResponse, User } from './types'

interface AuthState {
  user: User | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (data: { email: string; password: string; full_name: string }) => Promise<void>
  /** Aplica una sesión que ya se obtuvo por otra vía (ej. tras restablecer
   * la contraseña), sin volver a llamar a /auth/login. */
  applySession: (session: TokenResponse) => void
  logout: () => void
}

const AuthContext = createContext<AuthState | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  const logout = useCallback(() => {
    setToken(null)
    setUser(null)
  }, [])

  // Un token guardado puede haber expirado; se valida contra /auth/me al arrancar.
  useEffect(() => {
    if (!getToken()) {
      setLoading(false)
      return
    }
    let cancelled = false
    api
      .me()
      .then((me) => {
        if (!cancelled) setUser(me)
      })
      .catch(() => {
        if (!cancelled) setToken(null)
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  // El cliente HTTP avisa cuando el backend responde 401 en cualquier petición.
  useEffect(() => {
    onUnauthorized.handler = () => setUser(null)
    return () => {
      onUnauthorized.handler = null
    }
  }, [])

  const login = useCallback(async (email: string, password: string) => {
    const result = await api.login({ email, password })
    setToken(result.access_token)
    setUser(result.user)
  }, [])

  const register = useCallback(
    async (data: { email: string; password: string; full_name: string }) => {
      const result = await api.register(data)
      setToken(result.access_token)
      setUser(result.user)
    },
    [],
  )

  const applySession = useCallback((session: TokenResponse) => {
    setToken(session.access_token)
    setUser(session.user)
  }, [])

  const value = useMemo(
    () => ({ user, loading, login, register, applySession, logout }),
    [user, loading, login, register, applySession, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthState {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth debe usarse dentro de <AuthProvider>')
  return context
}
