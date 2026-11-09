/**
 * Cliente HTTP centralizado (Axios).
 * - Agrega el token JWT a cada petición.
 * - Si el backend responde 401 (token vencido o inválido), cierra la sesión.
 */
import axios from 'axios'

export const TOKEN_KEY = 'vitalcare_token'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_KEY)
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const isLogin = error.config?.url?.includes('/auth/login')
    if (error.response?.status === 401 && !isLogin) {
      localStorage.removeItem(TOKEN_KEY)
      window.dispatchEvent(new Event('vitalcare:logout'))
    }
    return Promise.reject(error)
  },
)

/** Convierte cualquier error de Axios en un mensaje legible para el usuario. */
export function getErrorMessage(error, fallback = 'Ocurrió un error inesperado') {
  if (!error?.response) {
    return 'No se pudo conectar con el servidor. Verifique que el backend esté en ejecución.'
  }
  const { status, data } = error.response
  if (status === 422 && Array.isArray(data?.errors) && data.errors.length) {
    return data.errors.map((e) => `${e.campo}: ${e.mensaje}`).join(' · ')
  }
  if (typeof data?.detail === 'string') return data.detail
  if (status === 403) return 'No tiene permisos para realizar esta operación'
  if (status === 404) return 'El recurso solicitado no existe'
  if (status >= 500) return 'Error interno del servidor. Intente de nuevo.'
  return fallback
}

/** Elimina parámetros vacíos antes de enviarlos como query string. */
export function cleanParams(params = {}) {
  return Object.fromEntries(
    Object.entries(params).filter(([, v]) => v !== '' && v !== null && v !== undefined),
  )
}

export default api
