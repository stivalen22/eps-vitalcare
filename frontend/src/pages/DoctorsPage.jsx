/** Médicos: CRUD para el administrador y directorio de consulta para pacientes. */
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { CalendarPlus, Pencil, Plus, Power, Stethoscope } from 'lucide-react'
import { doctorsApi, specialtiesApi } from '../api/services'
import { getErrorMessage } from '../api/client'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import { useFetch } from '../hooks/useFetch'
import { useListState } from '../hooks/useListState'
import { DataTable, Pagination } from '../components/DataTable'
import { ConfirmDialog, Modal } from '../components/Modal'
import { ActiveBadge, Badge, EmptyState, ErrorState, Field, Loader, Notice, PageHeader, SearchInput } from '../components/ui'
import { isEmail, isStrongPassword } from '../utils/format'

export default function DoctorsPage() {
  const { user } = useAuth()
  const isAdmin = user.rol === 'admin'
  const toast = useToast()
  const list = useListState({ activo: '', especialidad_id: '' }, isAdmin ? 10 : 12)
  const { data, loading, error, reload } = useFetch(() => doctorsApi.list(list.params), [list.paramsKey])
  const { data: specialties } = useFetch(() => specialtiesApi.list(), [])

  const [editing, setEditing] = useState(null)
  const [toggle, setToggle] = useState(null)
  const [toggling, setToggling] = useState(false)

  const confirmToggle = async () => {
    setToggling(true)
    try {
      await doctorsApi.setStatus(toggle.id, !toggle.activo)
      toast.success(toggle.activo ? 'Médico desactivado' : 'Médico reactivado')
      setToggle(null)
      reload()
    } catch (err) {
      toast.error(getErrorMessage(err))
      setToggle(null)
    } finally {
      setToggling(false)
    }
  }

  const filters = (
    <div className="toolbar">
      <SearchInput value={list.search} onChange={list.setSearch} placeholder="Buscar médico" />
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
        <PageHeader title="Médicos" subtitle="Profesionales disponibles (datos de demostración)" />
        <div className="card">{filters}</div>
        {loading ? (
          <Loader />
        ) : error ? (
          <ErrorState message={error} onRetry={reload} />
        ) : !data.items.length ? (
          <EmptyState title="No se encontraron médicos" />
        ) : (
          <div className="cards-grid">
            {data.items.map((m) => (
              <article key={m.id} className="card doctor-card">
                <div className="stat-icon tone-primary">
                  <Stethoscope size={22} aria-hidden="true" />
                </div>
                <h3>
                  {m.nombres} {m.apellidos}
                </h3>
                <div className="tag-list">
                  {m.especialidades.map((e) => (
                    <Badge key={e.id} tone="info">
                      {e.nombre}
                    </Badge>
                  ))}
                </div>
                <Link to="/citas/nueva" className="btn btn-secondary btn-sm">
                  <CalendarPlus size={16} /> Solicitar cita
                </Link>
              </article>
            ))}
          </div>
        )}
        {data && <Pagination page={list.page} size={list.size} total={data.total} onChange={list.setPage} />}
      </>
    )
  }

  const columns = [
    { key: 'nombre', header: 'Médico', render: (m) => `${m.nombres} ${m.apellidos}` },
    {
      key: 'especialidades',
      header: 'Especialidades',
      render: (m) => m.especialidades.map((e) => e.nombre).join(', '),
    },
    { key: 'registro_profesional', header: 'Identificador' },
    { key: 'email', header: 'Correo' },
    { key: 'activo', header: 'Estado', render: (m) => <ActiveBadge activo={m.activo} /> },
    {
      key: 'acciones',
      header: 'Acciones',
      className: 'actions',
      render: (m) => (
        <div className="row-actions">
          <Link className="icon-btn" title="Ver agenda" aria-label="Ver agenda" to={`/agenda?medico=${m.id}`}>
            <CalendarPlus size={17} />
          </Link>
          <button className="icon-btn" title="Editar" aria-label="Editar" onClick={() => setEditing(m)}>
            <Pencil size={17} />
          </button>
          <button
            className={`icon-btn ${m.activo ? 'danger' : 'success'}`}
            title={m.activo ? 'Desactivar' : 'Reactivar'}
            aria-label={m.activo ? 'Desactivar' : 'Reactivar'}
            onClick={() => setToggle(m)}
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
        title="Médicos"
        subtitle="Gestión de profesionales, especialidades y estado"
        actions={
          <button className="btn btn-primary" onClick={() => setEditing('new')}>
            <Plus size={18} /> Nuevo médico
          </button>
        }
      />
      <div className="card">
        {filters}
        <DataTable columns={columns} rows={data?.items} loading={loading} error={error} onRetry={reload} />
        {data && <Pagination page={list.page} size={list.size} total={data.total} onChange={list.setPage} />}
      </div>

      {editing && (
        <DoctorFormModal
          doctor={editing === 'new' ? null : editing}
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
        title={toggle?.activo ? 'Desactivar médico' : 'Reactivar médico'}
        message={
          toggle?.activo
            ? 'El médico no podrá iniciar sesión ni recibir nuevas citas. Si tiene citas programadas, primero debe cancelarlas o reprogramarlas.'
            : 'El médico volverá a estar disponible para recibir citas.'
        }
        confirmText={toggle?.activo ? 'Desactivar' : 'Reactivar'}
        loading={toggling}
        onConfirm={confirmToggle}
        onCancel={() => setToggle(null)}
      />
    </>
  )
}

function DoctorFormModal({ doctor, specialties, onClose, onSaved }) {
  const toast = useToast()
  const isNew = !doctor
  const [form, setForm] = useState({
    nombres: doctor?.nombres || '',
    apellidos: doctor?.apellidos || '',
    email: doctor?.email || '',
    telefono: doctor?.telefono || '',
    registro_profesional: doctor?.registro_profesional || '',
    especialidad_ids: doctor?.especialidades.map((e) => e.id) || [],
    password: '',
  })
  const [errors, setErrors] = useState({})
  const [serverError, setServerError] = useState('')
  const [saving, setSaving] = useState(false)

  const onChange = (e) => setForm({ ...form, [e.target.name]: e.target.value })
  const toggleSpecialty = (id) =>
    setForm((f) => ({
      ...f,
      especialidad_ids: f.especialidad_ids.includes(id)
        ? f.especialidad_ids.filter((x) => x !== id)
        : [...f.especialidad_ids, id],
    }))

  const submit = async (e) => {
    e.preventDefault()
    const errs = {}
    if (form.nombres.trim().length < 2) errs.nombres = 'Mínimo 2 caracteres'
    if (form.apellidos.trim().length < 2) errs.apellidos = 'Mínimo 2 caracteres'
    if (!isEmail(form.email)) errs.email = 'Correo inválido'
    if (!/^[0-9+\- ]{7,20}$/.test(form.telefono)) errs.telefono = 'Entre 7 y 20 dígitos'
    if (form.registro_profesional.trim().length < 4) errs.registro_profesional = 'Mínimo 4 caracteres'
    if (!form.especialidad_ids.length) errs.especialidad_ids = 'Seleccione al menos una especialidad'
    if (isNew && !isStrongPassword(form.password)) errs.password = 'Mínimo 8 caracteres, con letras y números'
    setErrors(errs)
    if (Object.keys(errs).length) return

    setSaving(true)
    setServerError('')
    try {
      const body = { ...form }
      if (!isNew) delete body.password
      if (isNew) await doctorsApi.create(body)
      else await doctorsApi.update(doctor.id, body)
      toast.success(isNew ? 'Médico creado correctamente' : 'Médico actualizado')
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
      size="lg"
      title={isNew ? 'Nuevo médico' : 'Editar médico'}
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
      <form onSubmit={submit} noValidate>
        {serverError && <Notice tone="danger">{serverError}</Notice>}
        <div className="form-grid">
          <Field label="Nombres" error={errors.nombres} required>
            <input name="nombres" value={form.nombres} onChange={onChange} />
          </Field>
          <Field label="Apellidos" error={errors.apellidos} required>
            <input name="apellidos" value={form.apellidos} onChange={onChange} />
          </Field>
          <Field label="Correo institucional (ficticio)" error={errors.email} required>
            <input name="email" type="email" value={form.email} onChange={onChange} />
          </Field>
          <Field label="Teléfono de demostración" error={errors.telefono} required>
            <input name="telefono" value={form.telefono} onChange={onChange} />
          </Field>
          <Field
            label="Identificador académico"
            error={errors.registro_profesional}
            required
            hint="Ficticio, no es un registro profesional real"
          >
            <input name="registro_profesional" value={form.registro_profesional} onChange={onChange} />
          </Field>
          {isNew && (
            <Field label="Contraseña inicial" error={errors.password} required>
              <input name="password" type="password" autoComplete="new-password" value={form.password} onChange={onChange} />
            </Field>
          )}
          <fieldset className="field span-2">
            <legend className="field-label">
              Especialidades <span className="required">*</span>
            </legend>
            <div className="checkbox-grid">
              {specialties.map((s) => (
                <label key={s.id} className="checkbox">
                  <input
                    type="checkbox"
                    checked={form.especialidad_ids.includes(s.id)}
                    onChange={() => toggleSpecialty(s.id)}
                  />
                  {s.nombre}
                </label>
              ))}
            </div>
            {errors.especialidad_ids && <span className="field-error">{errors.especialidad_ids}</span>}
          </fieldset>
        </div>
      </form>
    </Modal>
  )
}
