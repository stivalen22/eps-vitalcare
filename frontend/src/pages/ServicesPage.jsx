/** Servicios médicos: CRUD para el administrador y catálogo para los demás roles. */
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { BriefcaseMedical, CalendarPlus, Clock, Pencil, Plus, Power } from 'lucide-react'
import { servicesApi, specialtiesApi } from '../api/services'
import { getErrorMessage } from '../api/client'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import { useFetch } from '../hooks/useFetch'
import { useListState } from '../hooks/useListState'
import { DataTable, Pagination } from '../components/DataTable'
import { ConfirmDialog, Modal } from '../components/Modal'
import { ActiveBadge, Badge, EmptyState, ErrorState, Field, Loader, Notice, PageHeader, SearchInput } from '../components/ui'

export default function ServicesPage() {
  const { user } = useAuth()
  const isAdmin = user.rol === 'admin'
  const toast = useToast()
  const list = useListState({ activo: '', especialidad_id: '' }, isAdmin ? 10 : 12)
  const { data, loading, error, reload } = useFetch(() => servicesApi.list(list.params), [list.paramsKey])
  const { data: specialties } = useFetch(() => specialtiesApi.list(), [])
  const [editing, setEditing] = useState(null)
  const [toggle, setToggle] = useState(null)
  const [busy, setBusy] = useState(false)

  const confirmToggle = async () => {
    setBusy(true)
    try {
      await servicesApi.setStatus(toggle.id, !toggle.activo)
      toast.success(toggle.activo ? 'Servicio desactivado' : 'Servicio activado')
      reload()
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setBusy(false)
      setToggle(null)
    }
  }

  const toolbar = (
    <div className="toolbar">
      <SearchInput value={list.search} onChange={list.setSearch} placeholder="Buscar servicio" />
      <select
        value={list.filters.especialidad_id}
        onChange={(e) => list.setFilter('especialidad_id', e.target.value)}
        aria-label="Especialidad"
      >
        <option value="">Todas las especialidades</option>
        {specialties?.map((s) => (
          <option key={s.id} value={s.id}>
            {s.nombre}
          </option>
        ))}
      </select>
      {isAdmin && (
        <select value={list.filters.activo} onChange={(e) => list.setFilter('activo', e.target.value)} aria-label="Estado">
          <option value="">Todos los estados</option>
          <option value="true">Activos</option>
          <option value="false">Inactivos</option>
        </select>
      )}
    </div>
  )

  if (!isAdmin) {
    return (
      <>
        <PageHeader
          title="Servicios médicos"
          subtitle="Servicios de ejemplo del prototipo (no representan cobertura real de una EPS)"
        />
        <div className="card">{toolbar}</div>
        {loading ? (
          <Loader />
        ) : error ? (
          <ErrorState message={error} onRetry={reload} />
        ) : !data.items.length ? (
          <EmptyState title="No se encontraron servicios" />
        ) : (
          <div className="cards-grid">
            {data.items.map((s) => (
              <article key={s.id} className="card service-card">
                <div className="stat-icon tone-primary">
                  <BriefcaseMedical size={22} aria-hidden="true" />
                </div>
                <h3>{s.nombre}</h3>
                <p className="muted">{s.descripcion || 'Sin descripción'}</p>
                <div className="tag-list">
                  <Badge tone="info">{s.especialidad_nombre}</Badge>
                  <Badge tone="neutral">
                    <Clock size={12} /> {s.duracion_minutos} min
                  </Badge>
                </div>
                {user.rol === 'paciente' && (
                  <Link to={`/citas/nueva?servicio=${s.id}`} className="btn btn-secondary btn-sm">
                    <CalendarPlus size={16} /> Solicitar cita
                  </Link>
                )}
              </article>
            ))}
          </div>
        )}
        {data && <Pagination page={list.page} size={list.size} total={data.total} onChange={list.setPage} />}
      </>
    )
  }

  const columns = [
    { key: 'nombre', header: 'Servicio' },
    { key: 'especialidad_nombre', header: 'Especialidad' },
    { key: 'duracion_minutos', header: 'Duración', render: (s) => `${s.duracion_minutos} min` },
    { key: 'descripcion', header: 'Descripción', render: (s) => s.descripcion || '—' },
    { key: 'activo', header: 'Estado', render: (s) => <ActiveBadge activo={s.activo} /> },
    {
      key: 'acciones',
      header: 'Acciones',
      className: 'actions',
      render: (s) => (
        <div className="row-actions">
          <button className="icon-btn" aria-label="Editar" title="Editar" onClick={() => setEditing(s)}>
            <Pencil size={17} />
          </button>
          <button
            className={`icon-btn ${s.activo ? 'danger' : 'success'}`}
            aria-label={s.activo ? 'Desactivar' : 'Activar'}
            title={s.activo ? 'Desactivar' : 'Activar'}
            onClick={() => setToggle(s)}
          >
            <Power size={17} />
          </button>
        </div>
      ),
    },
  ]

  return (
    <>
      <PageHeader
        title="Servicios médicos"
        subtitle="Los servicios con historial no se eliminan: se desactivan"
        actions={
          <button className="btn btn-primary" onClick={() => setEditing('new')}>
            <Plus size={18} /> Nuevo servicio
          </button>
        }
      />
      <div className="card">
        {toolbar}
        <DataTable columns={columns} rows={data?.items} loading={loading} error={error} onRetry={reload} />
        {data && <Pagination page={list.page} size={list.size} total={data.total} onChange={list.setPage} />}
      </div>
      {editing && (
        <ServiceModal
          service={editing === 'new' ? null : editing}
          specialties={(specialties || []).filter((s) => s.activo)}
          onClose={() => setEditing(null)}
          onSaved={() => {
            setEditing(null)
            reload()
          }}
        />
      )}
      <ConfirmDialog
        open={!!toggle}
        danger={toggle?.activo}
        title={toggle?.activo ? 'Desactivar servicio' : 'Activar servicio'}
        message={
          toggle?.activo
            ? 'No se podrán solicitar nuevas citas de este servicio. Las citas existentes se conservan.'
            : 'El servicio volverá a estar disponible.'
        }
        confirmText={toggle?.activo ? 'Desactivar' : 'Activar'}
        loading={busy}
        onConfirm={confirmToggle}
        onCancel={() => setToggle(null)}
      />
    </>
  )
}

function ServiceModal({ service, specialties, onClose, onSaved }) {
  const toast = useToast()
  const [form, setForm] = useState({
    nombre: service?.nombre || '',
    descripcion: service?.descripcion || '',
    especialidad_id: service?.especialidad_id || '',
    duracion_minutos: service?.duracion_minutos || 30,
  })
  const [errors, setErrors] = useState({})
  const [serverError, setServerError] = useState('')
  const [saving, setSaving] = useState(false)
  const onChange = (e) => setForm({ ...form, [e.target.name]: e.target.value })

  const submit = async (e) => {
    e.preventDefault()
    const errs = {}
    const dur = Number(form.duracion_minutos)
    if (form.nombre.trim().length < 3) errs.nombre = 'Mínimo 3 caracteres'
    if (!form.especialidad_id) errs.especialidad_id = 'Seleccione una especialidad'
    if (!Number.isInteger(dur) || dur < 10 || dur > 240) errs.duracion_minutos = 'Entre 10 y 240 minutos'
    setErrors(errs)
    if (Object.keys(errs).length) return
    setSaving(true)
    setServerError('')
    try {
      const body = {
        nombre: form.nombre.trim(),
        descripcion: form.descripcion.trim() || null,
        especialidad_id: Number(form.especialidad_id),
        duracion_minutos: dur,
      }
      if (service) await servicesApi.update(service.id, body)
      else await servicesApi.create(body)
      toast.success('Servicio guardado')
      onSaved()
    } catch (err) {
      setServerError(getErrorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  return (
    <Modal
      open
      title={service ? 'Editar servicio' : 'Nuevo servicio'}
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
      <form onSubmit={submit} className="stack" noValidate>
        {serverError && <Notice tone="danger">{serverError}</Notice>}
        <Field label="Nombre" error={errors.nombre} required>
          <input name="nombre" value={form.nombre} maxLength={100} onChange={onChange} />
        </Field>
        <Field label="Especialidad" error={errors.especialidad_id} required>
          <select name="especialidad_id" value={form.especialidad_id} onChange={onChange}>
            <option value="">Seleccione...</option>
            {specialties.map((s) => (
              <option key={s.id} value={s.id}>
                {s.nombre}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Duración estimada (minutos)" error={errors.duracion_minutos} required>
          <input name="duracion_minutos" type="number" min={10} max={240} step={5} value={form.duracion_minutos} onChange={onChange} />
        </Field>
        <Field label="Descripción">
          <textarea name="descripcion" rows={3} maxLength={500} value={form.descripcion} onChange={onChange} />
        </Field>
      </form>
    </Modal>
  )
}
