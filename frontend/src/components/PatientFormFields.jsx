/** Campos compartidos por el registro público y el formulario administrativo de pacientes. */
import { Field } from './ui'
import { DOC_TYPES, isEmail, isStrongPassword, todayISO } from '../utils/format'

export const EMPTY_PATIENT = {
  email: '',
  password: '',
  tipo_documento: 'CC',
  numero_documento: '',
  nombres: '',
  apellidos: '',
  fecha_nacimiento: '',
  telefono: '',
  direccion: '',
}

/** Validación en el navegador (el backend vuelve a validar todo). */
export function validatePatient(form, { requirePassword = true } = {}) {
  const e = {}
  if (!isEmail(form.email)) e.email = 'Correo electrónico inválido'
  if (requirePassword && !isStrongPassword(form.password))
    e.password = 'Mínimo 8 caracteres, con al menos una letra y un número'
  if (!/^[0-9A-Za-z]{4,20}$/.test(form.numero_documento)) e.numero_documento = 'Entre 4 y 20 letras o números'
  if (form.nombres.trim().length < 2) e.nombres = 'Mínimo 2 caracteres'
  if (form.apellidos.trim().length < 2) e.apellidos = 'Mínimo 2 caracteres'
  if (!form.fecha_nacimiento) e.fecha_nacimiento = 'Obligatoria'
  else if (form.fecha_nacimiento > todayISO()) e.fecha_nacimiento = 'No puede ser futura'
  if (!/^[0-9+\- ]{7,20}$/.test(form.telefono)) e.telefono = 'Entre 7 y 20 dígitos'
  return e
}

export function PatientFormFields({ form, errors, onChange, showPassword = true }) {
  return (
    <div className="form-grid">
      <Field label="Nombres" error={errors.nombres} required>
        <input name="nombres" value={form.nombres} onChange={onChange} maxLength={80} />
      </Field>
      <Field label="Apellidos" error={errors.apellidos} required>
        <input name="apellidos" value={form.apellidos} onChange={onChange} maxLength={80} />
      </Field>
      <Field label="Tipo de documento" required>
        <select name="tipo_documento" value={form.tipo_documento} onChange={onChange}>
          {DOC_TYPES.map((d) => (
            <option key={d.value} value={d.value}>
              {d.label}
            </option>
          ))}
        </select>
      </Field>
      <Field label="Número de documento" error={errors.numero_documento} required hint="Use datos ficticios">
        <input name="numero_documento" value={form.numero_documento} onChange={onChange} maxLength={20} />
      </Field>
      <Field label="Fecha de nacimiento" error={errors.fecha_nacimiento} required>
        <input name="fecha_nacimiento" type="date" max={todayISO()} value={form.fecha_nacimiento} onChange={onChange} />
      </Field>
      <Field label="Teléfono" error={errors.telefono} required>
        <input name="telefono" value={form.telefono} onChange={onChange} maxLength={20} />
      </Field>
      <Field label="Correo electrónico" error={errors.email} required>
        <input name="email" type="email" value={form.email} onChange={onChange} maxLength={120} />
      </Field>
      {showPassword && (
        <Field label="Contraseña" error={errors.password} required hint="Mínimo 8 caracteres, letras y números">
          <input name="password" type="password" autoComplete="new-password" value={form.password} onChange={onChange} />
        </Field>
      )}
      <Field label="Dirección" error={errors.direccion} className="span-2">
        <input name="direccion" value={form.direccion} onChange={onChange} maxLength={150} />
      </Field>
    </div>
  )
}

/** Convierte los campos vacíos opcionales en null antes de enviarlos. */
export function toPatientPayload(form, { includePassword = true } = {}) {
  const payload = { ...form, direccion: form.direccion?.trim() || null }
  if (!includePassword) delete payload.password
  return payload
}
