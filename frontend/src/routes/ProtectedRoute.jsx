/**
 * Protege rutas en el navegador (comodidad de interfaz).
 * La protección real está en el backend: aunque alguien manipule el frontend,
 * la API responde 401/403.
 */
import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { Loader } from '../components/ui'
import ForbiddenPage from '../pages/ForbiddenPage'

export function ProtectedRoute({ roles }) {
  const { user, loading } = useAuth()
  const location = useLocation()
  if (loading) return <Loader text="Verificando sesión..." />
  if (!user) return <Navigate to="/login" replace state={{ from: location }} />
  if (roles && !roles.includes(user.rol)) return <ForbiddenPage />
  return <Outlet />
}

export function PublicOnlyRoute() {
  const { user, loading } = useAuth()
  if (loading) return <Loader />
  return user ? <Navigate to="/" replace /> : <Outlet />
}
