/**
 * Estado de autenticación. El rol mostrado aquí solo sirve para la interfaz:
 * el backend vuelve a verificar permisos en cada petición.
 */
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { TOKEN_KEY } from '../api/client'
import { authApi } from '../api/services'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY)
    setUser(null)
  }, [])

  const refreshUser = useCallback(async () => {
    const me = await authApi.me()
    setUser(me)
    return me
  }, [])

  // Al cargar la app, si hay token se valida contra /auth/me
  useEffect(() => {
    const token = localStorage.getItem(TOKEN_KEY)
    if (!token) {
      setLoading(false)
      return
    }
    refreshUser()
      .catch(() => logout())
      .finally(() => setLoading(false))
  }, [refreshUser, logout])

  // El interceptor de Axios emite este evento cuando el token deja de ser válido
  useEffect(() => {
    const handler = () => setUser(null)
    window.addEventListener('vitalcare:logout', handler)
    return () => window.removeEventListener('vitalcare:logout', handler)
  }, [])

  const login = useCallback(async (email, password) => {
    const res = await authApi.login(email, password)
    localStorage.setItem(TOKEN_KEY, res.access_token)
    setUser(res.user)
    return res.user
  }, [])

  const register = useCallback(async (payload) => {
    const res = await authApi.register(payload)
    localStorage.setItem(TOKEN_KEY, res.access_token)
    setUser(res.user)
    return res.user
  }, [])

  const value = useMemo(
    () => ({ user, loading, login, register, logout, refreshUser, setUser }),
    [user, loading, login, register, logout, refreshUser],
  )
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth debe usarse dentro de AuthProvider')
  return ctx
}
