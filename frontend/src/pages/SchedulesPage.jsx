/** Horarios de disponibilidad. El médico gestiona los suyos; el administrador, los de cualquier médico. */
import { useState } from 'react'
import { Pencil, Plus, Trash2 } from 'lucide-react'
import { doctorsApi, schedulesApi } from '../api/services'
import { getErrorMessage } from '../api/client'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import { useFetch } from '../hooks/useFetch'
import { DataTable } from '../components/DataTable'
import { ConfirmDialog, Modal } from '../components/Modal'
import { ActiveBadge, Field, Notice, PageHeader } from '../components/ui'
import { DAYS, formatTime } from '../utils/format'

export default function SchedulesPage() {
  const { user } = useAuth()
  const isAdmin = user.rol === 'admin'
  const toast = useToast()
  const [medicoId, setMedicoId] = useState('')
  const { data, loading, error, reload } = useFetch(() => schedulesApi.list({ medico_id: medicoId }), [medicoId])
  const { data: doctors } = useFetch(
    () => (isAdmin ? doctorsApi.list({ size: 100, activo: true }) : Promise.resolve({ items: [] })),
    [],
  )
  const [editing, setEditing] = useState(null)
  const [removing, setRemoving] = useState(null)
  const [busy, setBusy] = useState(false)

  const confirmRemove = async () => {
    setBusy(true)
    try {
      await schedulesApi.remove(removing.id)
      toast.success('Franja eliminada')
      reload()
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setBusy(false)
      setRemoving(null)
    }
  }

  const columns = [
    ...(isAdmin ? [{ key: 'medico_nombre', header: 'Médico' }] : []),
    { key: 'dia_nombre', header: 'Día' },
    {
      key: 'horas',
      header: 'Horario',
      render: (h) => `${formatTime(h.hora_inicio)} – ${formatTime(h.hora_fin)}`,
    },
    { key: 'duracion_cita_minutos', header: 'Intervalo', render: (h) => `cada ${h.duracion_cita_minutos} min` },
    { key: 'activo', header: 'Estado', render: (h) => <ActiveBadge activo={h.activo} /> },
    {
      key: 'acciones',
      header: 'Acciones',
      className: 'actions',
      render: (h) => (
        <div className="row-actions">
          <button className="icon-btn" aria-label="Editar" title="Editar" onClick={() => setEditing(h)}>
            <Pencil size={17} />
          </button>
          <button className="icon-btn danger" aria-label="Eliminar" title="Eliminar" onClick={() => setRemoving(h)}>
            <Trash2 size={17} />
          </button>
        </div>
      ),
    },
  ]

  return (
    <>
      <PageHeader
        title={isAdmin ? 'Horarios de los médicos' : 'Mi disponibilidad'}
        subtitle="Franjas semanales en las que se pueden asignar citas"
        actions={
          <button className="btn btn-primary" onClick={() => setEditing('new')}>
            <Plus size={18} /> Nueva franja
          </button>
        }
      />
      <div className="card">
        {isAdmin && (
          <div className="toolbar">
            <select value={medicoId} onChange={(e) => setMedicoId(e.target.value)} aria-label="Médico">
              <option value="">Todos los médicos</option>
              {doctors?.items.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.nombres} {d.apellidos}
                </option>
              ))}
            </select>
          </div>
        )}
        <DataTable
          columns={columns}
          rows={data}
          loading={loading}
          error={error}
          onRetry={reload}
          emptyTitle="No hay franjas registradas"
        />
      </div>
      {editing && (
        <ScheduleModal
          schedule={editing === 'new' ? null : editing}
          doctors={doctors?.items || []}
          isAdmin={isAdmin}
          defaultMedico={medicoId}
          onClose={() => setEditing(null)}
          onSaved={() => {
            setEditing(null)
            reload()
          }}
        />
      )}
      <ConfirmDialog
        open={!!removing}
        danger
        title="Eliminar franja"
        message="Solo se puede eliminar si no hay citas programadas dentro de esta franja."
        confirmText="Eliminar"
        loading={busy}
        onConfirm={confirmRemove}
        onCancel={() => setRemoving(null)}
      />
    </>
  )
}

function ScheduleModal({ schedule, doctors, isAdmin, defaultMedico, onClose, onSaved }) {
  const toast = useToast()
  const [form, setForm] = useState({
    medico_id: schedule?.medico_id || defaultMedico || '',
    dia_semana: schedule?.dia_semana ?? 0,
    hora_inicio: schedule ? formatTime(schedule.hora_inicio) : '08:00',
    hora_fin: schedule ? formatTime(schedule.hora_fin) : '12:00',
    duracion_cita_minutos: schedule?.duracion_cita_minutos || 30,
    activo: schedule?.activo ?? true,
  })
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)
  const onChange = (e) => setForm({ ...form, [e.target.name]: e.target.value })

  const submit = async (e) => {
    e.preventDefault()
    if (isAdmin && !form.medico_id) return setError('Seleccione el médico')
    if (form.hora_fin <= form.hora_inicio) return setError('La hora de finalización debe ser posterior a la de inicio')
    setSaving(true)
    setError('')
    try {
      const body = {
        medico_id: isAdmin ? Number(form.medico_id) : null,
        dia_semana: Number(form.dia_semana),
        hora_inicio: form.hora_inicio,
        hora_fin: form.hora_fin,
        duracion_cita_minutos: Number(form.duracion_cita_minutos),
        activo: form.activo,
      }
      if (schedule) await schedulesApi.update(schedule.id, body)
      else await schedulesApi.create(body)
      toast.success('Horario guardado')
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
      title={schedule ? 'Editar franja' : 'Nueva franja de disponibilidad'}
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
      <form onSubmit={submit} className="form-grid" noValidate>
        {error && (
          <div className="span-2">
            <Notice tone="danger">{error}</Notice>
          </div>
        )}
        {isAdmin && (
          <Field label="Médico" required className="span-2">
            <select name="medico_id" value={form.medico_id} onChange={onChange} disabled={!!schedule}>
              <option value="">Seleccione...</option>
              {doctors.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.nombres} {d.apellidos}
                </option>
              ))}
            </select>
          </Field>
        )}
        <Field label="Día de la semana" required>
          <select name="dia_semana" value={form.dia_semana} onChange={onChange}>
            {DAYS.map((d, i) => (
              <option key={d} value={i}>
                {d}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Intervalo entre citas (min)" required>
          <input name="duracion_cita_minutos" type="number" min={10} max={240} step={5} value={form.duracion_cita_minutos} onChange={onChange} />
        </Field>
        <Field label="Hora de inicio" required>
          <input name="hora_inicio" type="time" value={form.hora_inicio} onChange={onChange} />
        </Field>
        <Field label="Hora de finalización" required>
          <input name="hora_fin" type="time" value={form.hora_fin} onChange={onChange} />
        </Field>
        <label className="checkbox span-2">
          <input type="checkbox" checked={form.activo} onChange={(e) => setForm({ ...form, activo: e.target.checked })} />
          Franja activa
        </label>
      </form>
    </Modal>
  )
}
