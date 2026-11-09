/** CRUD de especialidades (administrador). */
import { useState } from 'react'
import { Pencil, Plus, Power } from 'lucide-react'
import { specialtiesApi } from '../api/services'
import { getErrorMessage } from '../api/client'
import { useFetch, useDebounce } from '../hooks/useFetch'
import { useToast } from '../context/ToastContext'
import { DataTable } from '../components/DataTable'
import { ConfirmDialog, Modal } from '../components/Modal'
import { ActiveBadge, Field, Notice, PageHeader, SearchInput } from '../components/ui'

export default function SpecialtiesPage() {
  const toast = useToast()
  const [search, setSearch] = useState('')
  const q = useDebounce(search)
  const { data, loading, error, reload } = useFetch(() => specialtiesApi.list({ q }), [q])
  const [editing, setEditing] = useState(null)
  const [toggle, setToggle] = useState(null)
  const [busy, setBusy] = useState(false)

  const confirmToggle = async () => {
    setBusy(true)
    try {
      await specialtiesApi.setStatus(toggle.id, !toggle.activo)
      toast.success('Estado actualizado')
      reload()
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setBusy(false)
      setToggle(null)
    }
  }

  const columns = [
    { key: 'nombre', header: 'Especialidad' },
    { key: 'descripcion', header: 'Descripción', render: (e) => e.descripcion || '—' },
    { key: 'activo', header: 'Estado', render: (e) => <ActiveBadge activo={e.activo} /> },
    {
      key: 'acciones',
      header: 'Acciones',
      className: 'actions',
      render: (e) => (
        <div className="row-actions">
          <button className="icon-btn" aria-label="Editar" title="Editar" onClick={() => setEditing(e)}>
            <Pencil size={17} />
          </button>
          <button
            className={`icon-btn ${e.activo ? 'danger' : 'success'}`}
            aria-label={e.activo ? 'Desactivar' : 'Activar'}
            title={e.activo ? 'Desactivar' : 'Activar'}
            onClick={() => setToggle(e)}
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
        title="Especialidades"
        subtitle="Áreas médicas de ejemplo usadas por médicos y servicios"
        actions={
          <button className="btn btn-primary" onClick={() => setEditing('new')}>
            <Plus size={18} /> Nueva especialidad
          </button>
        }
      />
      <div className="card">
        <div className="toolbar">
          <SearchInput value={search} onChange={setSearch} placeholder="Buscar especialidad" />
        </div>
        <DataTable columns={columns} rows={data} loading={loading} error={error} onRetry={reload} />
      </div>
      {editing && (
        <SpecialtyModal
          specialty={editing === 'new' ? null : editing}
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
        title={toggle?.activo ? 'Desactivar especialidad' : 'Activar especialidad'}
        message={
          toggle?.activo
            ? 'Solo se puede desactivar si no tiene servicios activos. Los registros históricos se conservan.'
            : 'La especialidad volverá a estar disponible.'
        }
        confirmText={toggle?.activo ? 'Desactivar' : 'Activar'}
        loading={busy}
        onConfirm={confirmToggle}
        onCancel={() => setToggle(null)}
      />
    </>
  )
}

function SpecialtyModal({ specialty, onClose, onSaved }) {
  const toast = useToast()
  const [form, setForm] = useState({ nombre: specialty?.nombre || '', descripcion: specialty?.descripcion || '' })
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    if (form.nombre.trim().length < 3) {
      setError('El nombre debe tener al menos 3 caracteres')
      return
    }
    setSaving(true)
    setError('')
    try {
      const body = { nombre: form.nombre.trim(), descripcion: form.descripcion.trim() || null }
      if (specialty) await specialtiesApi.update(specialty.id, body)
      else await specialtiesApi.create(body)
      toast.success('Especialidad guardada')
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
      title={specialty ? 'Editar especialidad' : 'Nueva especialidad'}
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
        {error && <Notice tone="danger">{error}</Notice>}
        <Field label="Nombre" required>
          <input value={form.nombre} maxLength={80} onChange={(e) => setForm({ ...form, nombre: e.target.value })} />
        </Field>
        <Field label="Descripción">
          <textarea
            rows={3}
            maxLength={255}
            value={form.descripcion}
            onChange={(e) => setForm({ ...form, descripcion: e.target.value })}
          />
        </Field>
      </form>
    </Modal>
  )
}
