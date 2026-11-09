/** Solicitudes de autorización: el paciente crea y consulta; el administrador revisa y cambia el estado. */
import { useState } from 'react'
import { History, Plus, RefreshCcw } from 'lucide-react'
import { authorizationsApi, servicesApi } from '../api/services'
import { getErrorMessage } from '../api/client'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import { useFetch } from '../hooks/useFetch'
import { useListState } from '../hooks/useListState'
import { DataTable, Pagination } from '../components/DataTable'
import { Modal } from '../components/Modal'
import { AuthorizationBadge, Field, Loader, Notice, PageHeader, SearchInput } from '../components/ui'
import { AUTH_STATUS, AUTH_TRANSITIONS, ROLE_LABELS, formatDateTime } from '../utils/format'

const STATUS_HELP = {
  pendiente: 'Tu solicitud fue recibida y espera revisión.',
  en_revision: 'El área administrativa está revisando tu solicitud.',
  aprobada: 'La solicitud fue aprobada (simulación académica, sin validez real).',
  rechazada: 'La solicitud fue rechazada. Revisa las observaciones.',
}

export default function AuthorizationsPage() {
  const { user } = useAuth()
  const isAdmin = user.rol === 'admin'
  const list = useListState({ estado: '' })
  const { data, loading, error, reload } = useFetch(() => authorizationsApi.list(list.params), [list.paramsKey])
  const [creating, setCreating] = useState(false)
  const [historyOf, setHistoryOf] = useState(null)
  const [updating, setUpdating] = useState(null)

  const columns = [
    { key: 'id', header: 'N.º' },
    ...(isAdmin ? [{ key: 'paciente_nombre', header: 'Paciente' }] : []),
    { key: 'servicio_nombre', header: 'Servicio' },
    { key: 'motivo', header: 'Motivo' },
    { key: 'creado_en', header: 'Solicitada', render: (a) => formatDateTime(a.creado_en) },
    {
      key: 'estado',
      header: 'Estado',
      render: (a) => (
        <div className="stack-xs">
          <AuthorizationBadge estado={a.estado} />
          {!isAdmin && <small className="muted">{STATUS_HELP[a.estado]}</small>}
          {a.observaciones && <small className="muted">Obs.: {a.observaciones}</small>}
        </div>
      ),
    },
    {
      key: 'acciones',
      header: 'Acciones',
      className: 'actions',
      render: (a) => (
        <div className="row-actions">
          <button className="icon-btn" title="Historial" aria-label="Ver historial" onClick={() => setHistoryOf(a)}>
            <History size={17} />
          </button>
          {isAdmin && AUTH_TRANSITIONS[a.estado].length > 0 && (
            <button className="icon-btn" title="Cambiar estado" aria-label="Cambiar estado" onClick={() => setUpdating(a)}>
              <RefreshCcw size={17} />
            </button>
          )}
        </div>
      ),
    },
  ]

  return (
    <>
      <PageHeader
        title={isAdmin ? 'Solicitudes de autorización' : 'Mis autorizaciones'}
        subtitle="Flujo académico ficticio: sin validez administrativa, clínica ni legal"
        actions={
          !isAdmin && (
            <button className="btn btn-primary" onClick={() => setCreating(true)}>
              <Plus size={18} /> Nueva solicitud
            </button>
          )
        }
      />
      <div className="card">
        <div className="toolbar">
          {isAdmin && <SearchInput value={list.search} onChange={list.setSearch} placeholder="Buscar paciente o servicio" />}
          <select value={list.filters.estado} onChange={(e) => list.setFilter('estado', e.target.value)} aria-label="Estado">
            <option value="">Todos los estados</option>
            {Object.entries(AUTH_STATUS).map(([k, v]) => (
              <option key={k} value={k}>
                {v.label}
              </option>
            ))}
          </select>
        </div>
        <DataTable
          columns={columns}
          rows={data?.items}
          loading={loading}
          error={error}
          onRetry={reload}
          emptyTitle="No hay solicitudes"
        />
        {data && <Pagination page={list.page} size={list.size} total={data.total} onChange={list.setPage} />}
      </div>

      {creating && (
        <CreateModal
          onClose={() => setCreating(false)}
          onSaved={() => {
            setCreating(false)
            reload()
          }}
        />
      )}
      {historyOf && <HistoryModal solicitud={historyOf} onClose={() => setHistoryOf(null)} />}
      {updating && (
        <StatusModal
          solicitud={updating}
          onClose={() => setUpdating(null)}
          onSaved={() => {
            setUpdating(null)
            reload()
          }}
        />
      )}
    </>
  )
}

function CreateModal({ onClose, onSaved }) {
  const toast = useToast()
  const { data: services } = useFetch(() => servicesApi.list({ size: 100 }), [])
  const [form, setForm] = useState({ servicio_id: '', motivo: '' })
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  const submit = async () => {
    if (!form.servicio_id) return setError('Seleccione el servicio')
    if (form.motivo.trim().length < 5) return setError('El motivo debe tener al menos 5 caracteres')
    setSaving(true)
    setError('')
    try {
      await authorizationsApi.create({ servicio_id: Number(form.servicio_id), motivo: form.motivo.trim() })
      toast.success('Solicitud enviada')
      onSaved()
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  return (
    <Modal
      open
      title="Nueva solicitud de autorización"
      onClose={onClose}
      footer={
        <>
          <button className="btn btn-secondary" onClick={onClose}>
            Cancelar
          </button>
          <button className="btn btn-primary" onClick={submit} disabled={saving}>
            {saving ? 'Enviando...' : 'Enviar solicitud'}
          </button>
        </>
      }
    >
      <div className="stack">
        {error && <Notice tone="danger">{error}</Notice>}
        <Field label="Servicio solicitado" required>
          <select value={form.servicio_id} onChange={(e) => setForm({ ...form, servicio_id: e.target.value })}>
            <option value="">Seleccione...</option>
            {services?.items.map((s) => (
              <option key={s.id} value={s.id}>
                {s.nombre}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Motivo administrativo" required hint="Breve, sin datos clínicos sensibles">
          <textarea rows={3} maxLength={255} value={form.motivo} onChange={(e) => setForm({ ...form, motivo: e.target.value })} />
        </Field>
      </div>
    </Modal>
  )
}

function HistoryModal({ solicitud, onClose }) {
  const { data, loading, error } = useFetch(() => authorizationsApi.history(solicitud.id), [solicitud.id])
  return (
    <Modal open title={`Historial de la solicitud N.º ${solicitud.id}`} onClose={onClose}>
      {loading ? (
        <Loader />
      ) : error ? (
        <Notice tone="danger">{error}</Notice>
      ) : (
        <ol className="timeline">
          {data.map((h) => (
            <li key={h.id}>
              <div className="timeline-head">
                {h.estado_anterior ? (
                  <>
                    <AuthorizationBadge estado={h.estado_anterior} /> → <AuthorizationBadge estado={h.estado_nuevo} />
                  </>
                ) : (
                  <AuthorizationBadge estado={h.estado_nuevo} />
                )}
              </div>
              <p className="small muted">
                {formatDateTime(h.creado_en)} · {h.usuario_nombre} ({ROLE_LABELS[h.usuario_rol]})
              </p>
              {h.observacion && <p>{h.observacion}</p>}
            </li>
          ))}
        </ol>
      )}
    </Modal>
  )
}

function StatusModal({ solicitud, onClose, onSaved }) {
  const toast = useToast()
  const options = AUTH_TRANSITIONS[solicitud.estado]
  const [estado, setEstado] = useState(options[0])
  const [obs, setObs] = useState('')
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  const submit = async () => {
    if (estado === 'rechazada' && !obs.trim()) return setError('Indique una observación para el rechazo')
    setSaving(true)
    setError('')
    try {
      await authorizationsApi.setStatus(solicitud.id, estado, obs.trim())
      toast.success('Estado actualizado. El paciente fue notificado.')
      onSaved()
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  return (
    <Modal
      open
      title="Actualizar estado"
      onClose={onClose}
      footer={
        <>
          <button className="btn btn-secondary" onClick={onClose}>
            Cancelar
          </button>
          <button className="btn btn-primary" onClick={submit} disabled={saving}>
            {saving ? 'Guardando...' : 'Guardar'}
          </button>
        </>
      }
    >
      <div className="stack">
        <p>
          <strong>{solicitud.paciente_nombre}</strong> · {solicitud.servicio_nombre}
        </p>
        <p className="muted">
          Estado actual: <AuthorizationBadge estado={solicitud.estado} />
        </p>
        {error && <Notice tone="danger">{error}</Notice>}
        <Field label="Nuevo estado" required>
          <select value={estado} onChange={(e) => setEstado(e.target.value)}>
            {options.map((s) => (
              <option key={s} value={s}>
                {AUTH_STATUS[s].label}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Observaciones" required={estado === 'rechazada'}>
          <textarea rows={3} maxLength={500} value={obs} onChange={(e) => setObs(e.target.value)} />
        </Field>
      </div>
    </Modal>
  )
}
