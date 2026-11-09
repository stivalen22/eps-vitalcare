/** Historial: consultas simuladas y citas pasadas (paciente) o consultas registradas (médico). */
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { appointmentsApi, consultationsApi } from '../api/services'
import { useAuth } from '../context/AuthContext'
import { useFetch } from '../hooks/useFetch'
import { DataTable, Pagination } from '../components/DataTable'
import { AppointmentBadge, Notice, PageHeader } from '../components/ui'
import { Modal } from '../components/Modal'
import { formatDate, formatDateTime, formatTime, todayISO } from '../utils/format'

export default function HistoryPage() {
  const { user } = useAuth()
  const isPatient = user.rol === 'paciente'
  const [tab, setTab] = useState('consultas')
  const [pageC, setPageC] = useState(1)
  const [pageA, setPageA] = useState(1)
  const [detail, setDetail] = useState(null)

  const consults = useFetch(() => consultationsApi.list({ page: pageC, size: 10 }), [pageC])
  const past = useFetch(
    () =>
      isPatient
        ? appointmentsApi.list({ fecha_hasta: todayISO(), page: pageA, size: 10, orden: 'desc' })
        : Promise.resolve(null),
    [pageA],
  )

  const consultColumns = [
    { key: 'fecha', header: 'Fecha', render: (c) => formatDate(c.fecha) },
    { key: 'servicio_nombre', header: 'Servicio' },
    isPatient
      ? { key: 'medico_nombre', header: 'Médico' }
      : { key: 'paciente_nombre', header: 'Paciente' },
    { key: 'resumen', header: 'Resumen', render: (c) => (c.resumen.length > 70 ? `${c.resumen.slice(0, 70)}…` : c.resumen) },
    {
      key: 'ver',
      header: '',
      className: 'actions',
      render: (c) => (
        <button className="btn btn-ghost btn-sm" onClick={() => setDetail(c)}>
          Ver
        </button>
      ),
    },
  ]
  const apptColumns = [
    { key: 'fecha', header: 'Fecha', render: (c) => `${formatDate(c.fecha)} ${formatTime(c.hora_inicio)}` },
    { key: 'servicio_nombre', header: 'Servicio' },
    { key: 'medico_nombre', header: 'Médico' },
    { key: 'estado', header: 'Estado', render: (c) => <AppointmentBadge estado={c.estado} /> },
    {
      key: 'ver',
      header: '',
      className: 'actions',
      render: (c) => (
        <Link className="btn btn-ghost btn-sm" to={`/citas/${c.id}`}>
          Detalle
        </Link>
      ),
    },
  ]

  return (
    <>
      <PageHeader
        title={isPatient ? 'Mi historial' : 'Consultas registradas'}
        subtitle="Registros simulados con fines académicos: no contienen diagnósticos ni prescripciones"
      />
      {isPatient && (
        <div className="tabs" role="tablist">
          <button role="tab" aria-selected={tab === 'consultas'} className={tab === 'consultas' ? 'active' : ''} onClick={() => setTab('consultas')}>
            Consultas
          </button>
          <button role="tab" aria-selected={tab === 'citas'} className={tab === 'citas' ? 'active' : ''} onClick={() => setTab('citas')}>
            Citas anteriores
          </button>
        </div>
      )}
      <div className="card">
        {tab === 'consultas' || !isPatient ? (
          <>
            <DataTable
              columns={consultColumns}
              rows={consults.data?.items}
              loading={consults.loading}
              error={consults.error}
              onRetry={consults.reload}
              emptyTitle="Aún no hay consultas registradas"
            />
            {consults.data && (
              <Pagination page={pageC} size={10} total={consults.data.total} onChange={setPageC} />
            )}
          </>
        ) : (
          <>
            <DataTable
              columns={apptColumns}
              rows={past.data?.items}
              loading={past.loading}
              error={past.error}
              onRetry={past.reload}
              emptyTitle="No hay citas anteriores"
            />
            {past.data && <Pagination page={pageA} size={10} total={past.data.total} onChange={setPageA} />}
          </>
        )}
      </div>

      <Modal open={!!detail} title="Detalle de la consulta" onClose={() => setDetail(null)}>
        {detail && (
          <>
            <Notice tone="info">Registro simulado con fines académicos.</Notice>
            <dl className="details">
              <dt>Fecha</dt>
              <dd>{formatDate(detail.fecha)}</dd>
              <dt>Paciente</dt>
              <dd>{detail.paciente_nombre}</dd>
              <dt>Médico</dt>
              <dd>{detail.medico_nombre}</dd>
              <dt>Servicio</dt>
              <dd>{detail.servicio_nombre}</dd>
              <dt>Resumen</dt>
              <dd>{detail.resumen}</dd>
              <dt>Observaciones</dt>
              <dd>{detail.observaciones || '—'}</dd>
              <dt>Registrada</dt>
              <dd>{formatDateTime(detail.creado_en)}</dd>
            </dl>
          </>
        )}
      </Modal>
    </>
  )
}
