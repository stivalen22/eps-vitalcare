/** Selector de espacios disponibles. Consulta /schedules/available-slots (ya excluye horarios ocupados). */
import { useFetch } from '../hooks/useFetch'
import { schedulesApi } from '../api/services'
import { ErrorState, Loader } from './ui'
import { formatTime } from '../utils/format'

export default function SlotPicker({ medicoId, servicioId, fecha, value, onChange }) {
  const ready = medicoId && servicioId && fecha
  const { data, loading, error, reload } = useFetch(
    () =>
      ready
        ? schedulesApi.slots({ medico_id: medicoId, servicio_id: servicioId, fecha })
        : Promise.resolve([]),
    [medicoId, servicioId, fecha],
  )

  if (!ready) return <p className="muted">Selecciona servicio, médico y fecha para ver los horarios disponibles.</p>
  if (loading) return <Loader text="Buscando horarios disponibles..." />
  if (error) return <ErrorState message={error} onRetry={reload} />
  if (!data.length)
    return (
      <p className="notice notice-warning">
        No hay horarios disponibles para esta fecha. El médico no atiende ese día o su agenda está llena; prueba otra fecha.
      </p>
    )
  return (
    <div className="slot-grid" role="radiogroup" aria-label="Horarios disponibles">
      {data.map((s) => {
        const v = formatTime(s.hora_inicio)
        return (
          <button
            type="button"
            key={v}
            role="radio"
            aria-checked={value === v}
            className={`slot ${value === v ? 'selected' : ''}`}
            onClick={() => onChange(v)}
          >
            {v}
          </button>
        )
      })}
    </div>
  )
}
