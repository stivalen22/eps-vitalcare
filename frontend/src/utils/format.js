/** Utilidades de formato y catálogos de etiquetas. */

export const ROLE_LABELS = { paciente: 'Paciente', medico: 'Médico', admin: 'Administrador' }

export const APPOINTMENT_STATUS = {
  pendiente: { label: 'Pendiente', tone: 'warning' },
  confirmada: { label: 'Confirmada', tone: 'info' },
  en_atencion: { label: 'En atención', tone: 'primary' },
  atendida: { label: 'Atendida', tone: 'success' },
  cancelada: { label: 'Cancelada', tone: 'danger' },
}

export const AUTH_STATUS = {
  pendiente: { label: 'Pendiente', tone: 'warning' },
  en_revision: { label: 'En revisión', tone: 'info' },
  aprobada: { label: 'Aprobada', tone: 'success' },
  rechazada: { label: 'Rechazada', tone: 'danger' },
}

/** Transiciones de estado de citas (deben coincidir con el backend). */
export const APPOINTMENT_TRANSITIONS = {
  pendiente: ['confirmada'],
  confirmada: ['en_atencion', 'atendida'],
  en_atencion: ['atendida'],
  atendida: [],
  cancelada: [],
}

export const AUTH_TRANSITIONS = {
  pendiente: ['en_revision', 'aprobada', 'rechazada'],
  en_revision: ['aprobada', 'rechazada'],
  aprobada: [],
  rechazada: [],
}

export const DAYS = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']

export const DOC_TYPES = [
  { value: 'CC', label: 'Cédula de ciudadanía' },
  { value: 'TI', label: 'Tarjeta de identidad' },
  { value: 'CE', label: 'Cédula de extranjería' },
  { value: 'PA', label: 'Pasaporte' },
  { value: 'RC', label: 'Registro civil' },
]

/** '2026-10-19' -> '19/10/2026' sin problemas de zona horaria. */
export function formatDate(iso) {
  if (!iso) return '—'
  const [y, m, d] = iso.slice(0, 10).split('-')
  return `${d}/${m}/${y}`
}

/** '2026-10-19' -> 'lun. 19 oct.' */
export function formatDateLong(iso) {
  if (!iso) return '—'
  const [y, m, d] = iso.slice(0, 10).split('-').map(Number)
  return new Date(y, m - 1, d).toLocaleDateString('es-CO', {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  })
}

/** '09:30:00' -> '09:30' */
export function formatTime(t) {
  return t ? t.slice(0, 5) : '—'
}

export function formatDateTime(iso) {
  if (!iso) return '—'
  return `${formatDate(iso)} ${iso.slice(11, 16)}`
}

/** Fecha local de hoy en formato AAAA-MM-DD. */
export function todayISO(offsetDays = 0) {
  const d = new Date()
  d.setDate(d.getDate() + offsetDays)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

export function isEmail(value) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)
}

export function isStrongPassword(value) {
  return value.length >= 8 && value.length <= 64 && /[A-Za-z]/.test(value) && /\d/.test(value)
}
