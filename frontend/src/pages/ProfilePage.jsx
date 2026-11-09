import { useState } from 'react'
import { KeyRound, Save } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import { authApi } from '../api/services'
import { getErrorMessage } from '../api/client'
import { Field, PageHeader } from '../components/ui'
import { ROLE_LABELS, formatDate, isStrongPassword } from '../utils/format'

export default function ProfilePage() {
  const { user, setUser } = useAuth()
  const toast = useToast()
  const profile = user.paciente || user.medico

  const [contact, setContact] = useState({
    telefono: profile?.telefono || '',
    direccion: user.paciente?.direccion || '',
  })
  const [saving, setSaving] = useState(false)
  const [pwd, setPwd] = useState({ current_password: '', new_password: '', confirm: '' })
  const [pwdErrors, setPwdErrors] = useState({})
  const [changing, setChanging] = useState(false)

  const saveContact = async (e) => {
    e.preventDefault()
    if (!/^[0-9+\- ]{7,20}$/.test(contact.telefono)) {
      toast.error('El teléfono debe tener entre 7 y 20 dígitos')
      return
    }
    setSaving(true)
    try {
      const payload = user.paciente
        ? { telefono: contact.telefono, direccion: contact.direccion || null }
        : { telefono: contact.telefono }
      setUser(await authApi.updateMe(payload))
      toast.success('Perfil actualizado')
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  const changePassword = async (e) => {
    e.preventDefault()
    const errs = {}
    if (!pwd.current_password) errs.current_password = 'Obligatoria'
    if (!isStrongPassword(pwd.new_password)) errs.new_password = 'Mínimo 8 caracteres, con letras y números'
    if (pwd.new_password !== pwd.confirm) errs.confirm = 'Las contraseñas no coinciden'
    setPwdErrors(errs)
    if (Object.keys(errs).length) return
    setChanging(true)
    try {
      await authApi.changePassword({ current_password: pwd.current_password, new_password: pwd.new_password })
      toast.success('Contraseña actualizada')
      setPwd({ current_password: '', new_password: '', confirm: '' })
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setChanging(false)
    }
  }

  return (
    <>
      <PageHeader title="Mi perfil" subtitle="Consulta tus datos y actualiza la información permitida" />
      <div className="grid-2">
        <section className="card">
          <h2>Datos de la cuenta</h2>
          <dl className="details">
            <dt>Nombre</dt>
            <dd>{user.nombre_completo}</dd>
            <dt>Correo</dt>
            <dd>{user.email}</dd>
            <dt>Rol</dt>
            <dd>{ROLE_LABELS[user.rol]}</dd>
            {user.paciente && (
              <>
                <dt>Documento</dt>
                <dd>
                  {user.paciente.tipo_documento} {user.paciente.numero_documento}
                </dd>
                <dt>Fecha de nacimiento</dt>
                <dd>{formatDate(user.paciente.fecha_nacimiento)}</dd>
              </>
            )}
            {user.medico && (
              <>
                <dt>Identificador académico</dt>
                <dd>{user.medico.registro_profesional}</dd>
                <dt>Especialidades</dt>
                <dd>{user.medico.especialidades.map((e) => e.nombre).join(', ')}</dd>
              </>
            )}
          </dl>
          {profile ? (
            <form onSubmit={saveContact} className="stack">
              <h3>Datos de contacto</h3>
              <Field label="Teléfono" required>
                <input value={contact.telefono} onChange={(e) => setContact({ ...contact, telefono: e.target.value })} />
              </Field>
              {user.paciente && (
                <Field label="Dirección">
                  <input
                    value={contact.direccion}
                    maxLength={150}
                    onChange={(e) => setContact({ ...contact, direccion: e.target.value })}
                  />
                </Field>
              )}
              <button className="btn btn-primary" disabled={saving}>
                <Save size={18} /> {saving ? 'Guardando...' : 'Guardar cambios'}
              </button>
              <p className="muted small">Para cambiar nombre, documento o correo, contacte al administrador.</p>
            </form>
          ) : (
            <p className="muted">La cuenta de administrador no tiene datos de contacto editables.</p>
          )}
        </section>

        <section className="card">
          <h2>Cambiar contraseña</h2>
          <form onSubmit={changePassword} className="stack" noValidate>
            <Field label="Contraseña actual" error={pwdErrors.current_password} required>
              <input
                type="password"
                autoComplete="current-password"
                value={pwd.current_password}
                onChange={(e) => setPwd({ ...pwd, current_password: e.target.value })}
              />
            </Field>
            <Field label="Nueva contraseña" error={pwdErrors.new_password} required>
              <input
                type="password"
                autoComplete="new-password"
                value={pwd.new_password}
                onChange={(e) => setPwd({ ...pwd, new_password: e.target.value })}
              />
            </Field>
            <Field label="Confirmar nueva contraseña" error={pwdErrors.confirm} required>
              <input
                type="password"
                autoComplete="new-password"
                value={pwd.confirm}
                onChange={(e) => setPwd({ ...pwd, confirm: e.target.value })}
              />
            </Field>
            <button className="btn btn-primary" disabled={changing}>
              <KeyRound size={18} /> {changing ? 'Actualizando...' : 'Actualizar contraseña'}
            </button>
          </form>
        </section>
      </div>
    </>
  )
}
