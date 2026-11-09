/** Listado de citas con búsqueda y filtros. El backend limita los resultados según el rol. */
import { Link } from 'react-router-dom'
import { CalendarPlus, Eye } from 'lucide-react'
import { appointmentsApi } from '../api/services'
import { useAuth } from '../context/AuthContext'
import { useFetch } from '../hooks/useFetch'
import { useListState } from '../hooks/useListState'
import { DataTable, Pagination } from '../components/DataTable'
import { AppointmentBadge, PageHeader, SearchInput } from '../components/ui'
import { APPOINTMENT_STATUS, formatDate, formatTime } from '../utils/format'

export default function AppointmentsPage() {
  const { user } = useAuth()
  const list = useListState({ estado: '', fecha_desde: '', fecha_hasta: '', orden: 'desc' })
  const { data, loading, error, reload } = useFetch(() => appointmentsApi.list(list.params), [list.paramsKey])

  const title = { paciente: 'Mis citas', medico: 'Citas asignadas', admin: 'Gestión de citas' }[user.rol]
  const columns = [
    {
      key: 'fecha',
      header: 'Fecha y hora',
      render: (c) => (
        <span className="nowrap">
          {formatDate(c.fecha)} · {formatTime(c.hora_inicio)}
        </span>
      ),
    },
    ...(user.rol !== 'paciente'
      ? [{ key: 'paciente', header: 'Paciente', render: (c) => `${c.paciente_nombre} (${c.paciente_documento})` }]
      : []),
    ...(user.rol !== 'medico' ? [{ key: 'medico_nombre', header: 'Médico' }] : []),
    { key: 'servicio_nombre', header: 'Servicio' },
    { key: 'motivo', header: 'Motivo' },
    { key: 'estado', header: 'Estado', render: (c) => <AppointmentBadge estado={c.estado} /> },
    {
      key: 'ver',
      header: '',
      className: 'actions',
      render: (c) => (
        <Link to={`/citas/${c.id}`} className="btn btn-ghost btn-sm">
          <Eye size={16} /> Detalle
        </Link>
      ),
    },
  ]

  return (
    <>
      <PageHeader
        title={title}
        subtitle="Filtra por estado o fechas y abre el detalle para gestionar cada cita"
        actions={
          user.rol !== 'medico' && (
            <Link to="/citas/nueva" className="btn btn-primary">
              <CalendarPlus size={18} /> {user.rol === 'admin' ? 'Asignar cita' : 'Solicitar cita'}
            </Link>
          )
        }
      />
      <div className="card">
        <div className="toolbar">
          {user.rol !== 'paciente' && (
            <SearchInput value={list.search} onChange={list.setSearch} placeholder="Buscar paciente, médico o servicio" />
          )}
          <select value={list.filters.estado} onChange={(e) => list.setFilter('estado', e.target.value)} aria-label="Estado">
            <option value="">Todos los estados</option>
            {Object.entries(APPOINTMENT_STATUS).map(([k, v]) => (
              <option key={k} value={k}>
                {v.label}
              </option>
            ))}
          </select>
          <label className="inline-field">
            Desde
            <input type="date" value={list.filters.fecha_desde} onChange={(e) => list.setFilter('fecha_desde', e.target.value)} />
          </label>
          <label className="inline-field">
            Hasta
            <input type="date" value={list.filters.fecha_hasta} onChange={(e) => list.setFilter('fecha_hasta', e.target.value)} />
          </label>
          <select value={list.filters.orden} onChange={(e) => list.setFilter('orden', e.target.value)} aria-label="Orden">
            <option value="desc">Más recientes primero</option>
            <option value="asc">Más antiguas primero</option>
          </select>
        </div>
        <DataTable
          columns={columns}
          rows={data?.items}
          loading={loading}
          error={error}
          onRetry={reload}
          emptyTitle="No hay citas"
          emptyMessage="Cambia los filtros o solicita una nueva cita."
        />
        {data && <Pagination page={list.page} size={list.size} total={data.total} onChange={list.setPage} />}
      </div>
    </>
  )
}
