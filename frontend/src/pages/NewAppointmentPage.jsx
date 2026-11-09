/** Solicitud de cita (paciente) o asignación (administrador). */
import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { CalendarCheck } from 'lucide-react'
import { appointmentsApi, patientsApi, servicesApi } from '../api/services'
import { getErrorMessage } from '../api/client'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import { useDebounce, useFetch } from '../hooks/useFetch'
import { Field, Loader, Notice, PageHeader } from '../components/ui'
import SlotPicker from '../components/SlotPicker'
import { todayISO } from '../utils/format'

export default function NewAppointmentPage() {
  const { user } = useAuth()
  const isAdmin = user.rol === 'admin'
  const toast = useToast()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()

  const [form, setForm] = useState({
    paciente_id: '',
    servicio_id: searchParams.get('servicio') || '',
    medico_id: '',
    fecha: todayISO(1),
    hora_inicio: '',
    motivo: '',
  })
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)
  const [slotsVersion, setSlotsVersion] = useState(0)
  const [patientSearch, setPatientSearch] = useState('')
  const q = useDebounce(patientSearch)

  const { data: services, loading: loadingServices } = useFetch(() => servicesApi.list({ size: 100 }), [])
  const { data: doctors } = useFetch(
    () => (form.servicio_id ? servicesApi.doctors(form.servicio_id) : Promise.resolve([])),
    [form.servicio_id],
  )
  const { data: patients } = useFetch(
    () => (isAdmin ? patientsApi.list({ q, activo: true, size: 20 }) : Promise.resolve({ items: [] })),
    [q],
  )

  // Si el servicio solo tiene un médico, se selecciona automáticamente
  useEffect(() => {
    if (doctors?.length === 1) setForm((f) => ({ ...f, medico_id: String(doctors[0].id) }))
  }, [doctors])

  const set = (key, value) =>
    setForm((f) => {
      const next = { ...f, [key]: value }
      if (key === 'servicio_id') next.medico_id = ''
      if (['servicio_id', 'medico_id', 'fecha'].includes(key)) next.hora_inicio = ''
      return next
    })

  const submit = async (e) => {
    e.preventDefault()
    if (isAdmin && !form.paciente_id) return setError('Seleccione el paciente')
    if (!form.servicio_id || !form.medico_id) return setError('Seleccione el servicio y el médico')
    if (!form.hora_inicio) return setError('Seleccione un horario disponible')
    if (form.motivo.trim().length < 3) return setError('Describa brevemente el motivo (mínimo 3 caracteres)')
    setSaving(true)
    setError('')
    try {
      const cita = await appointmentsApi.create({
        paciente_id: isAdmin ? Number(form.paciente_id) : null,
        servicio_id: Number(form.servicio_id),
        medico_id: Number(form.medico_id),
        fecha: form.fecha,
        hora_inicio: form.hora_inicio,
        motivo: form.motivo.trim(),
      })
      toast.success('Cita registrada correctamente')
      navigate(`/citas/${cita.id}`)
    } catch (err) {
      // Ej.: 409 si otra persona tomó el horario mientras se completaba el formulario
      setError(getErrorMessage(err))
      setForm((f) => ({ ...f, hora_inicio: '' }))
      setSlotsVersion((v) => v + 1) // vuelve a consultar los horarios libres
    } finally {
      setSaving(false)
    }
  }

  if (loadingServices) return <Loader />

  return (
    <>
      <PageHeader
        title={isAdmin ? 'Asignar cita' : 'Solicitar cita'}
        subtitle="Elige el servicio, el profesional y un horario disponible"
      />
      <form className="card stack" onSubmit={submit} noValidate>
        {error && <Notice tone="danger">{error}</Notice>}

        {isAdmin && (
          <div className="form-grid">
            <Field label="Buscar paciente">
              <input
                value={patientSearch}
                onChange={(e) => setPatientSearch(e.target.value)}
                placeholder="Nombre o documento"
              />
            </Field>
            <Field label="Paciente" required>
              <select value={form.paciente_id} onChange={(e) => set('paciente_id', e.target.value)}>
                <option value="">Seleccione...</option>
                {patients?.items.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.nombres} {p.apellidos} · {p.tipo_documento} {p.numero_documento}
                  </option>
                ))}
              </select>
            </Field>
          </div>
        )}

        <div className="form-grid">
          <Field label="1. Servicio" required>
            <select value={form.servicio_id} onChange={(e) => set('servicio_id', e.target.value)}>
              <option value="">Seleccione...</option>
              {services?.items.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.nombre} ({s.duracion_minutos} min)
                </option>
              ))}
            </select>
          </Field>
          <Field label="2. Médico" required>
            <select
              value={form.medico_id}
              onChange={(e) => set('medico_id', e.target.value)}
              disabled={!form.servicio_id}
            >
              <option value="">{form.servicio_id ? 'Seleccione...' : 'Primero elija un servicio'}</option>
              {doctors?.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.nombres} {d.apellidos}
                </option>
              ))}
            </select>
          </Field>
          <Field label="3. Fecha" required>
            <input type="date" min={todayISO()} value={form.fecha} onChange={(e) => set('fecha', e.target.value)} />
          </Field>
        </div>

        <div>
          <p className="field-label">4. Horario disponible</p>
          <SlotPicker
            key={slotsVersion}
            medicoId={form.medico_id}
            servicioId={form.servicio_id}
            fecha={form.fecha}
            value={form.hora_inicio}
            onChange={(v) => set('hora_inicio', v)}
          />
        </div>

        <Field label="5. Motivo de la cita" required hint="Descripción breve, sin datos clínicos sensibles">
          <textarea rows={2} maxLength={255} value={form.motivo} onChange={(e) => set('motivo', e.target.value)} />
        </Field>

        <div className="form-actions">
          <button type="button" className="btn btn-secondary" onClick={() => navigate(-1)}>
            Cancelar
          </button>
          <button className="btn btn-primary" disabled={saving}>
            <CalendarCheck size={18} /> {saving ? 'Registrando...' : 'Confirmar solicitud'}
          </button>
        </div>
      </form>
    </>
  )
}
