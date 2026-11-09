/** Detalle de una cita con las acciones permitidas según rol y estado. */
import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ArrowLeft, CalendarClock, CheckCircle2, ClipboardPen, XCircle } from 'lucide-react'
import { appointmentsApi, consultationsApi, servicesApi } from '../api/services'
import { getErrorMessage } from '../api/client'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import { useFetch } from '../hooks/useFetch'
import { ConfirmDialog, Modal } from '../components/Modal'
import { AppointmentBadge, ErrorState, Field, Loader, Notice, PageHeader } from '../components/ui'
import SlotPicker from '../components/SlotPicker'
import {
  APPOINTMENT_STATUS,
  APPOINTMENT_TRANSITIONS,
  formatDateLong,
  formatDateTime,
  formatTime,
  todayISO,
} from '../utils/format'

export default function AppointmentDetailPage() {
  const { id } = useParams()
  const { user } = useAuth()
  const toast = useToast()
  const { data: cita, loading, error, reload, setData } = useFetch(() => appointmentsApi.get(id), [id])
  const canSeeConsult = user.rol !== 'admin'
  const { data: consult, reload: reloadConsult } = useFetch(
    () => (canSeeConsult ? consultationsApi.list({ cita_id: id }) : Promise.resolve(null)),
    [id],
  )

  const [nextState, setNextState] = useState(null)
  const [cancelOpen, setCancelOpen] = useState(false)
  const [cancelReason, setCancelReason] = useState('')
  const [reprogramOpen, setReprogramOpen] = useState(false)
  const [consultOpen, setConsultOpen] = useState(false)
  const [busy, setBusy] = useState(false)

  if (loading) return <Loader />
  if (error) return <ErrorState message={error} onRetry={reload} />

  const today = todayISO()
  const isScheduled = ['pendiente', 'confirmada'].includes(cita.estado)
  const nowTime = new Date().toTimeString().slice(0, 8) // hora local HH:MM:SS
  const isFuture = `${cita.fecha}T${cita.hora_inicio}` > `${today}T${nowTime}`
  const transitions =
    user.rol === 'paciente'
      ? []
      : APPOINTMENT_TRANSITIONS[cita.estado].filter((s) => !(['en_atencion', 'atendida'].includes(s) && cita.fecha > today))
  const canCancel = isScheduled && (user.rol !== 'paciente' || isFuture)
  const canReprogram = isScheduled && user.rol !== 'medico'
  const canConsult =
    user.rol === 'medico' &&
    ['confirmada', 'en_atencion', 'atendida'].includes(cita.estado) &&
    cita.fecha <= today &&
    !cita.tiene_consulta

  const run = async (fn, okMsg) => {
    setBusy(true)
    try {
      const updated = await fn()
      setData(updated)
      toast.success(okMsg)
      return true
    } catch (err) {
      toast.error(getErrorMessage(err))
      return false
    } finally {
      setBusy(false)
    }
  }

  const consulta = consult?.items?.[0]

  return (
    <>
      <PageHeader
        title={`Cita #${cita.id}`}
        subtitle={`${cita.servicio_nombre} · ${formatDateLong(cita.fecha)} a las ${formatTime(cita.hora_inicio)}`}
        actions={
          <Link to="/citas" className="btn btn-secondary">
            <ArrowLeft size={18} /> Volver
          </Link>
        }
      />
      <div className="grid-2">
        <section className="card">
          <div className="card-title-row">
            <h2>Información</h2>
            <AppointmentBadge estado={cita.estado} />
          </div>
          <dl className="details">
            <dt>Paciente</dt>
            <dd>
              {cita.paciente_nombre} ({cita.paciente_documento})
            </dd>
            <dt>Médico</dt>
            <dd>{cita.medico_nombre}</dd>
            <dt>Servicio</dt>
            <dd>{cita.servicio_nombre}</dd>
            <dt>Fecha</dt>
            <dd>{formatDateLong(cita.fecha)}</dd>
            <dt>Horario</dt>
            <dd>
              {formatTime(cita.hora_inicio)} – {formatTime(cita.hora_fin)}
            </dd>
            <dt>Motivo</dt>
            <dd>{cita.motivo}</dd>
            {cita.estado === 'cancelada' && (
              <>
                <dt>Motivo de cancelación</dt>
                <dd>{cita.motivo_cancelacion || '—'}</dd>
              </>
            )}
            <dt>Registrada</dt>
            <dd>{formatDateTime(cita.creado_en)}</dd>
          </dl>
        </section>

        <section className="card">
          <h2>Acciones</h2>
          {!transitions.length && !canCancel && !canReprogram && !canConsult && (
            <p className="muted">No hay acciones disponibles para esta cita en su estado actual.</p>
          )}
          <div className="action-list">
            {transitions.map((s) => (
              <button key={s} className="btn btn-primary" disabled={busy} onClick={() => setNextState(s)}>
                <CheckCircle2 size={18} /> Marcar como {APPOINTMENT_STATUS[s].label.toLowerCase()}
              </button>
            ))}
            {canConsult && (
              <button className="btn btn-primary" onClick={() => setConsultOpen(true)}>
                <ClipboardPen size={18} /> Registrar consulta
              </button>
            )}
            {canReprogram && (
              <button className="btn btn-secondary" onClick={() => setReprogramOpen(true)}>
                <CalendarClock size={18} /> Reprogramar
              </button>
            )}
            {canCancel && (
              <button className="btn btn-danger" onClick={() => setCancelOpen(true)}>
                <XCircle size={18} /> Cancelar cita
              </button>
            )}
          </div>
          {user.rol === 'paciente' && isScheduled && !isFuture && (
            <Notice tone="warning">La hora de la cita ya pasó; no puede cancelarse desde tu cuenta.</Notice>
          )}

          {canSeeConsult && consulta && (
            <div className="consult-box">
              <h3>Consulta registrada (simulada)</h3>
              <p>{consulta.resumen}</p>
              {consulta.observaciones && <p className="muted">{consulta.observaciones}</p>}
              <p className="small muted">Registrada el {formatDateTime(consulta.creado_en)}</p>
            </div>
          )}
          {user.rol === 'admin' && (
            <p className="small muted">
              Por privacidad, el rol administrador no visualiza el contenido de las consultas.
            </p>
          )}
        </section>
      </div>

      <ConfirmDialog
        open={!!nextState}
        title="Cambiar estado"
        message={nextState && `¿Marcar la cita como "${APPOINTMENT_STATUS[nextState].label}"?`}
        loading={busy}
        onConfirm={async () => {
          await run(() => appointmentsApi.setStatus(cita.id, nextState), 'Estado actualizado')
          setNextState(null)
        }}
        onCancel={() => setNextState(null)}
      />

      <ConfirmDialog
        open={cancelOpen}
        danger
        title="Cancelar cita"
        message="La cita quedará cancelada y se conservará en el historial. El horario se liberará."
        confirmText="Cancelar cita"
        loading={busy}
        onConfirm={async () => {
          const ok = await run(() => appointmentsApi.cancel(cita.id, cancelReason.trim()), 'Cita cancelada')
          if (ok) setCancelOpen(false)
        }}
        onCancel={() => setCancelOpen(false)}
      >
        <Field label="Motivo (opcional)">
          <input value={cancelReason} maxLength={255} onChange={(e) => setCancelReason(e.target.value)} />
        </Field>
      </ConfirmDialog>

      {reprogramOpen && (
        <ReprogramModal
          cita={cita}
          onClose={() => setReprogramOpen(false)}
          onSaved={(updated) => {
            setData(updated)
            setReprogramOpen(false)
          }}
        />
      )}

      {consultOpen && (
        <ConsultationModal
          cita={cita}
          onClose={() => setConsultOpen(false)}
          onSaved={() => {
            setConsultOpen(false)
            reload()
            reloadConsult()
          }}
        />
      )}
    </>
  )
}

function ReprogramModal({ cita, onClose, onSaved }) {
  const toast = useToast()
  const { data: doctors } = useFetch(() => servicesApi.doctors(cita.servicio_id), [cita.servicio_id])
  const [form, setForm] = useState({
    medico_id: String(cita.medico_id),
    fecha: cita.fecha,
    hora_inicio: '',
    motivo: cita.motivo,
  })
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  const submit = async () => {
    if (!form.hora_inicio) return setError('Seleccione un horario disponible')
    setSaving(true)
    setError('')
    try {
      const updated = await appointmentsApi.update(cita.id, { ...form, medico_id: Number(form.medico_id) })
      toast.success('Cita reprogramada. Queda pendiente de confirmación.')
      onSaved(updated)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  return (
    <Modal
      open
      size="lg"
      title="Reprogramar cita"
      onClose={onClose}
      footer={
        <>
          <button className="btn btn-secondary" onClick={onClose}>
            Cancelar
          </button>
          <button className="btn btn-primary" onClick={submit} disabled={saving}>
            {saving ? 'Guardando...' : 'Guardar cambios'}
          </button>
        </>
      }
    >
      <div className="stack">
        {error && <Notice tone="danger">{error}</Notice>}
        <div className="form-grid">
          <Field label="Médico">
            <select
              value={form.medico_id}
              onChange={(e) => setForm({ ...form, medico_id: e.target.value, hora_inicio: '' })}
            >
              {doctors?.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.nombres} {d.apellidos}
                </option>
              ))}
            </select>
          </Field>
          <Field label="Nueva fecha">
            <input
              type="date"
              min={todayISO()}
              value={form.fecha}
              onChange={(e) => setForm({ ...form, fecha: e.target.value, hora_inicio: '' })}
            />
          </Field>
        </div>
        <SlotPicker
          medicoId={form.medico_id}
          servicioId={cita.servicio_id}
          fecha={form.fecha}
          value={form.hora_inicio}
          onChange={(v) => setForm({ ...form, hora_inicio: v })}
        />
        <Field label="Motivo">
          <input value={form.motivo} maxLength={255} onChange={(e) => setForm({ ...form, motivo: e.target.value })} />
        </Field>
      </div>
    </Modal>
  )
}

function ConsultationModal({ cita, onClose, onSaved }) {
  const toast = useToast()
  const [form, setForm] = useState({ resumen: '', observaciones: '' })
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  const submit = async () => {
    if (form.resumen.trim().length < 10) return setError('El resumen debe tener al menos 10 caracteres')
    setSaving(true)
    setError('')
    try {
      await consultationsApi.create({
        cita_id: cita.id,
        resumen: form.resumen.trim(),
        observaciones: form.observaciones.trim() || null,
      })
      toast.success('Consulta registrada. La cita quedó como atendida.')
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
      title="Registrar consulta (simulada)"
      onClose={onClose}
      footer={
        <>
          <button className="btn btn-secondary" onClick={onClose}>
            Cancelar
          </button>
          <button className="btn btn-primary" onClick={submit} disabled={saving}>
            {saving ? 'Guardando...' : 'Guardar consulta'}
          </button>
        </>
      }
    >
      <div className="stack">
        <Notice tone="info">
          Registro académico ficticio. No incluya diagnósticos reales, recetas ni datos de personas reales.
        </Notice>
        {error && <Notice tone="danger">{error}</Notice>}
        <Field label="Resumen de la consulta" required>
          <textarea rows={4} maxLength={2000} value={form.resumen} onChange={(e) => setForm({ ...form, resumen: e.target.value })} />
        </Field>
        <Field label="Observaciones">
          <textarea
            rows={3}
            maxLength={2000}
            value={form.observaciones}
            onChange={(e) => setForm({ ...form, observaciones: e.target.value })}
          />
        </Field>
      </div>
    </Modal>
  )
}
