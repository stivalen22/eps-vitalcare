/** Agenda semanal tipo calendario (médico: la propia; administrador: la del médico elegido). */
import { useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { ChevronLeft, ChevronRight } from 'lucide-react'
import { appointmentsApi, doctorsApi } from '../api/services'
import { useAuth } from '../context/AuthContext'
import { useFetch } from '../hooks/useFetch'
import { ErrorState, Loader, PageHeader } from '../components/ui'
import { APPOINTMENT_STATUS, DAYS, formatTime, todayISO } from '../utils/format'

function iso(d) {
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

function mondayOf(date) {
  const d = new Date(date)
  const diff = (d.getDay() + 6) % 7 // lunes = 0
  d.setDate(d.getDate() - diff)
  return d
}

export default function AgendaPage() {
  const { user } = useAuth()
  const isAdmin = user.rol === 'admin'
  const [params, setParams] = useSearchParams()
  const medicoId = isAdmin ? params.get('medico') || '' : String(user.medico?.id || '')
  const [weekStart, setWeekStart] = useState(() => mondayOf(new Date()))

  const days = Array.from({ length: 7 }, (_, i) => {
    const d = new Date(weekStart)
    d.setDate(d.getDate() + i)
    return iso(d)
  })

  const { data: doctors } = useFetch(
    () => (isAdmin ? doctorsApi.list({ size: 100 }) : Promise.resolve({ items: [] })),
    [],
  )
  const { data, loading, error, reload } = useFetch(
    () =>
      medicoId
        ? appointmentsApi.list({ medico_id: medicoId, fecha_desde: days[0], fecha_hasta: days[6], size: 100, orden: 'asc' })
        : Promise.resolve({ items: [] }),
    [medicoId, days[0]],
  )

  const moveWeek = (delta) => {
    const d = new Date(weekStart)
    d.setDate(d.getDate() + delta * 7)
    setWeekStart(d)
  }

  const byDay = Object.fromEntries(days.map((d) => [d, []]))
  data?.items.forEach((c) => byDay[c.fecha]?.push(c))

  return (
    <>
      <PageHeader title="Agenda semanal" subtitle="Vista de calendario de las citas de la semana" />
      <div className="card">
        <div className="toolbar">
          {isAdmin && (
            <select
              value={medicoId}
              onChange={(e) => setParams(e.target.value ? { medico: e.target.value } : {})}
              aria-label="Médico"
            >
              <option value="">Seleccione un médico...</option>
              {doctors?.items.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.nombres} {d.apellidos}
                </option>
              ))}
            </select>
          )}
          <div className="week-nav">
            <button className="btn btn-secondary btn-sm" onClick={() => moveWeek(-1)} aria-label="Semana anterior">
              <ChevronLeft size={16} />
            </button>
            <button className="btn btn-secondary btn-sm" onClick={() => setWeekStart(mondayOf(new Date()))}>
              Hoy
            </button>
            <button className="btn btn-secondary btn-sm" onClick={() => moveWeek(1)} aria-label="Semana siguiente">
              <ChevronRight size={16} />
            </button>
            <strong>
              {days[0].split('-').reverse().join('/')} – {days[6].split('-').reverse().join('/')}
            </strong>
          </div>
        </div>

        {!medicoId ? (
          <p className="muted">Seleccione un médico para ver su agenda.</p>
        ) : loading ? (
          <Loader />
        ) : error ? (
          <ErrorState message={error} onRetry={reload} />
        ) : (
          <div className="week-grid">
            {days.map((d, i) => (
              <div key={d} className={`week-day ${d === todayISO() ? 'today' : ''}`}>
                <div className="week-day-head">
                  <span>{DAYS[i]}</span>
                  <strong>{d.slice(8, 10)}</strong>
                </div>
                {byDay[d].length === 0 && <p className="muted small">Sin citas</p>}
                {byDay[d].map((c) => (
                  <Link key={c.id} to={`/citas/${c.id}`} className={`week-appt tone-${APPOINTMENT_STATUS[c.estado].tone}`}>
                    <strong>
                      {formatTime(c.hora_inicio)}–{formatTime(c.hora_fin)}
                    </strong>
                    <span>{c.paciente_nombre}</span>
                    <small>
                      {c.servicio_nombre} · {APPOINTMENT_STATUS[c.estado].label}
                    </small>
                  </Link>
                ))}
              </div>
            ))}
          </div>
        )}
      </div>
    </>
  )
}
