/** Lista compacta de citas para paneles. */
import { Link } from 'react-router-dom'
import { Clock } from 'lucide-react'
import { AppointmentBadge, EmptyState } from './ui'
import { formatDateLong, formatTime } from '../utils/format'

export default function AppointmentList({ items, show = 'medico', emptyText = 'No hay citas para mostrar' }) {
  if (!items?.length) return <EmptyState title={emptyText} />
  return (
    <ul className="appt-list">
      {items.map((c) => (
        <li key={c.id}>
          <Link to={`/citas/${c.id}`} className="appt-item">
            <div className="appt-time">
              <Clock size={16} aria-hidden="true" />
              <span>{formatTime(c.hora_inicio)}</span>
            </div>
            <div className="appt-main">
              <strong>{c.servicio_nombre}</strong>
              <span className="muted">
                {formatDateLong(c.fecha)} · {show === 'medico' ? c.medico_nombre : c.paciente_nombre}
              </span>
            </div>
            <AppointmentBadge estado={c.estado} />
          </Link>
        </li>
      ))}
    </ul>
  )
}
