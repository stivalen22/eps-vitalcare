/** Registro de auditoría (solo lectura). */
import { auditApi } from '../api/services'
import { useFetch } from '../hooks/useFetch'
import { useListState } from '../hooks/useListState'
import { DataTable, Pagination } from '../components/DataTable'
import { Badge, PageHeader } from '../components/ui'
import { formatDateTime } from '../utils/format'

const RECURSOS = ['sesion', 'usuario', 'paciente', 'medico', 'especialidad', 'servicio', 'horario', 'cita', 'consulta', 'autorizacion']
const ACCIONES = ['login', 'registro', 'crear', 'actualizar', 'activar', 'desactivar', 'cambiar_estado', 'cancelar', 'eliminar', 'cambiar_rol', 'cambio_contrasena', 'actualizar_perfil']

export default function AuditPage() {
  const list = useListState({ recurso: '', accion: '', fecha_desde: '', fecha_hasta: '' }, 20)
  const { data, loading, error, reload } = useFetch(() => auditApi.list(list.params), [list.paramsKey])

  const columns = [
    { key: 'creado_en', header: 'Fecha y hora', render: (a) => formatDateTime(a.creado_en) },
    { key: 'usuario_email', header: 'Usuario', render: (a) => a.usuario_email || 'Anónimo' },
    { key: 'accion', header: 'Acción' },
    { key: 'recurso', header: 'Recurso', render: (a) => `${a.recurso}${a.recurso_id ? ` #${a.recurso_id}` : ''}` },
    {
      key: 'resultado',
      header: 'Resultado',
      render: (a) => <Badge tone={a.resultado === 'exito' ? 'success' : 'danger'}>{a.resultado}</Badge>,
    },
    { key: 'detalle', header: 'Detalle', render: (a) => a.detalle || '—' },
  ]

  return (
    <>
      <PageHeader
        title="Auditoría"
        subtitle="Registro básico de acciones. No es un sistema certificado de cumplimiento normativo."
      />
      <div className="card">
        <div className="toolbar">
          <select value={list.filters.recurso} onChange={(e) => list.setFilter('recurso', e.target.value)} aria-label="Recurso">
            <option value="">Todos los recursos</option>
            {RECURSOS.map((r) => (
              <option key={r}>{r}</option>
            ))}
          </select>
          <select value={list.filters.accion} onChange={(e) => list.setFilter('accion', e.target.value)} aria-label="Acción">
            <option value="">Todas las acciones</option>
            {ACCIONES.map((a) => (
              <option key={a}>{a}</option>
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
        </div>
        <DataTable columns={columns} rows={data?.items} loading={loading} error={error} onRetry={reload} />
        {data && <Pagination page={list.page} size={list.size} total={data.total} onChange={list.setPage} />}
      </div>
    </>
  )
}
