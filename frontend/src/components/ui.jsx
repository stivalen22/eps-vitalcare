/** Componentes de interfaz pequeños y reutilizables. */
import { AlertTriangle, Inbox, Loader2, RefreshCw, Search } from 'lucide-react'
import { APPOINTMENT_STATUS, AUTH_STATUS } from '../utils/format'

export function Loader({ text = 'Cargando...' }) {
  return (
    <div className="loader" role="status">
      <Loader2 className="spin" size={22} aria-hidden="true" />
      <span>{text}</span>
    </div>
  )
}

export function EmptyState({ title = 'Sin registros', message, action }) {
  return (
    <div className="empty-state">
      <Inbox size={36} aria-hidden="true" />
      <h3>{title}</h3>
      {message && <p>{message}</p>}
      {action}
    </div>
  )
}

export function ErrorState({ message, onRetry }) {
  return (
    <div className="error-state" role="alert">
      <AlertTriangle size={28} aria-hidden="true" />
      <p>{message}</p>
      {onRetry && (
        <button className="btn btn-secondary" onClick={onRetry}>
          <RefreshCw size={16} /> Reintentar
        </button>
      )}
    </div>
  )
}

export function Badge({ tone = 'neutral', children }) {
  return <span className={`badge badge-${tone}`}>{children}</span>
}

export function AppointmentBadge({ estado }) {
  const s = APPOINTMENT_STATUS[estado] || { label: estado, tone: 'neutral' }
  return <Badge tone={s.tone}>{s.label}</Badge>
}

export function AuthorizationBadge({ estado }) {
  const s = AUTH_STATUS[estado] || { label: estado, tone: 'neutral' }
  return <Badge tone={s.tone}>{s.label}</Badge>
}

export function ActiveBadge({ activo }) {
  return <Badge tone={activo ? 'success' : 'neutral'}>{activo ? 'Activo' : 'Inactivo'}</Badge>
}

export function PageHeader({ title, subtitle, actions }) {
  return (
    <div className="page-header">
      <div>
        <h1>{title}</h1>
        {subtitle && <p className="muted">{subtitle}</p>}
      </div>
      {actions && <div className="page-actions">{actions}</div>}
    </div>
  )
}

export function StatCard({ icon: Icon, label, value, hint, tone = 'primary' }) {
  return (
    <div className="card stat-card">
      <div className={`stat-icon tone-${tone}`}>{Icon && <Icon size={22} aria-hidden="true" />}</div>
      <div>
        <p className="stat-label">{label}</p>
        <p className="stat-value">{value}</p>
        {hint && <p className="stat-hint">{hint}</p>}
      </div>
    </div>
  )
}

/** Campo de formulario con etiqueta y mensaje de error. */
export function Field({ label, error, required, children, hint, className = '' }) {
  return (
    <label className={`field ${error ? 'has-error' : ''} ${className}`}>
      <span className="field-label">
        {label} {required && <span className="required" aria-hidden="true">*</span>}
      </span>
      {children}
      {hint && !error && <span className="field-hint">{hint}</span>}
      {error && <span className="field-error">{error}</span>}
    </label>
  )
}

export function SearchInput({ value, onChange, placeholder = 'Buscar...' }) {
  return (
    <div className="search-input">
      <Search size={16} aria-hidden="true" />
      <input
        type="search"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        aria-label={placeholder}
      />
    </div>
  )
}

export function Notice({ tone = 'info', children }) {
  return <div className={`notice notice-${tone}`}>{children}</div>
}
