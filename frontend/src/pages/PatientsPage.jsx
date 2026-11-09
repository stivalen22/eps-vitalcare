/** CRUD administrativo de pacientes. */
import { useState } from 'react'
import { Eye, Pencil, Plus, Power } from 'lucide-react'
import { patientsApi } from '../api/services'
import { getErrorMessage } from '../api/client'
import { useFetch } from '../hooks/useFetch'
import { useListState } from '../hooks/useListState'
import { useToast } from '../context/ToastContext'
import { DataTable, Pagination } from '../components/DataTable'
import { ConfirmDialog, Modal } from '../components/Modal'
import { ActiveBadge, Notice, PageHeader, SearchInput } from '../components/ui'
import { EMPTY_PATIENT, PatientFormFields, toPatientPayload, validatePatient } from '../components/PatientFormFields'
import { formatDate, formatDateTime } from '../utils/format'

export default function PatientsPage() {
  const toast = useToast()
  const list = useListState({ activo: '' })
  const { data, loading, error, reload } = useFetch(() => patientsApi.list(list.params), [list.paramsKey])

  const [editing, setEditing] = useState(null) // null | 'new' | paciente
  const [detail, setDetail] = useState(null)
  const [toggle, setToggle] = useState(null)
  const [toggling, setToggling] = useState(false)

  const confirmToggle = async () => {
    setToggling(true)
    try {
      await patientsApi.setStatus(toggle.id, !toggle.activo)
      toast.success(toggle.activo ? 'Paciente desactivado' : 'Paciente reactivado')
      setToggle(null)
      reload()
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setToggling(false)
    }
  }

  const columns = [
    { key: 'nombre', header: 'Paciente', render: (p) => `${p.nombres} ${p.apellidos}` },
    { key: 'documento', header: 'Documento', render: (p) => `${p.tipo_documento} ${p.numero_documento}` },
    { key: 'email', header: 'Correo' },
    { key: 'telefono', header: 'Teléfono' },
    { key: 'activo', header: 'Estado', render: (p) => <ActiveBadge activo={p.activo} /> },
    {
      key: 'acciones',
      header: 'Acciones',
      className: 'actions',
      render: (p) => (
        <div className="row-actions">
          <button className="icon-btn" title="Ver detalle" aria-label="Ver detalle" onClick={() => setDetail(p)}>
            <Eye size={17} />
          </button>
          <button className="icon-btn" title="Editar" aria-label="Editar" onClick={() => setEditing(p)}>
            <Pencil size={17} />
          </button>
          <button
            className={`icon-btn ${p.activo ? 'danger' : 'success'}`}
            title={p.activo ? 'Desactivar' : 'Reactivar'}
            aria-label={p.activo ? 'Desactivar' : 'Reactivar'}
            onClick={() => setToggle(p)}
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
        title="Pacientes"
        subtitle="Registro, edición y estado de las cuentas de pacientes"
        actions={
          <button className="btn btn-primary" onClick={() => setEditing('new')}>
            <Plus size={18} /> Nuevo paciente
          </button>
        }
      />
      <div className="card">
        <div className="toolbar">
          <SearchInput value={list.search} onChange={list.setSearch} placeholder="Buscar por nombre, documento o correo" />
          <select value={list.filters.activo} onChange={(e) => list.setFilter('activo', e.target.value)} aria-label="Estado">
            <option value="">Todos los estados</option>
            <option value="true">Activos</option>
            <option value="false">Inactivos</option>
          </select>
        </div>
        <DataTable
          columns={columns}
          rows={data?.items}
          loading={loading}
          error={error}
          onRetry={reload}
          emptyTitle="No se encontraron pacientes"
        />
        {data && <Pagination page={list.page} size={list.size} total={data.total} onChange={list.setPage} />}
      </div>

      {editing && (
        <PatientFormModal
          patient={editing === 'new' ? null : editing}
          onClose={() => setEditing(null)}
          onSaved={() => {
            setEditing(null)
            reload()
          }}
        />
      )}

      <Modal open={!!detail} title="Detalle del paciente" onClose={() => setDetail(null)}>
        {detail && (
          <dl className="details">
            <dt>Nombre</dt>
            <dd>
              {detail.nombres} {detail.apellidos}
            </dd>
            <dt>Documento</dt>
            <dd>
              {detail.tipo_documento} {detail.numero_documento}
            </dd>
            <dt>Fecha de nacimiento</dt>
            <dd>{formatDate(detail.fecha_nacimiento)}</dd>
            <dt>Correo</dt>
            <dd>{detail.email}</dd>
            <dt>Teléfono</dt>
            <dd>{detail.telefono}</dd>
            <dt>Dirección</dt>
            <dd>{detail.direccion || '—'}</dd>
            <dt>Estado</dt>
            <dd>
              <ActiveBadge activo={detail.activo} />
            </dd>
            <dt>Creado</dt>
            <dd>{formatDateTime(detail.creado_en)}</dd>
          </dl>
        )}
      </Modal>

      <ConfirmDialog
        open={!!toggle}
        danger={toggle?.activo}
        title={toggle?.activo ? 'Desactivar paciente' : 'Reactivar paciente'}
        message={
          toggle?.activo
            ? `${toggle?.nombres} ${toggle?.apellidos} no podrá iniciar sesión. Su historial se conserva.`
            : `${toggle?.nombres} ${toggle?.apellidos} podrá volver a iniciar sesión.`
        }
        confirmText={toggle?.activo ? 'Desactivar' : 'Reactivar'}
        loading={toggling}
        onConfirm={confirmToggle}
        onCancel={() => setToggle(null)}
      />
    </>
  )
}

function PatientFormModal({ patient, onClose, onSaved }) {
  const toast = useToast()
  const isNew = !patient
  const [form, setForm] = useState(
    isNew ? EMPTY_PATIENT : { ...EMPTY_PATIENT, ...patient, direccion: patient.direccion || '', password: '' },
  )
  const [errors, setErrors] = useState({})
  const [serverError, setServerError] = useState('')
  const [saving, setSaving] = useState(false)

  const onChange = (e) => setForm({ ...form, [e.target.name]: e.target.value })

  const submit = async (e) => {
    e.preventDefault()
    const errs = validatePatient(form, { requirePassword: isNew })
    setErrors(errs)
    if (Object.keys(errs).length) return
    setSaving(true)
    setServerError('')
    try {
      const payload = toPatientPayload(form, { includePassword: isNew })
      const fields = [
        'email', 'password', 'tipo_documento', 'numero_documento', 'nombres',
        'apellidos', 'fecha_nacimiento', 'telefono', 'direccion',
      ]
      const body = Object.fromEntries(fields.filter((f) => f in payload).map((f) => [f, payload[f]]))
      if (isNew) await patientsApi.create(body)
      else await patientsApi.update(patient.id, body)
      toast.success(isNew ? 'Paciente creado correctamente' : 'Paciente actualizado')
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
      title={isNew ? 'Nuevo paciente' : 'Editar paciente'}
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
        <PatientFormFields form={form} errors={errors} onChange={onChange} showPassword={isNew} />
      </form>
    </Modal>
  )
}
