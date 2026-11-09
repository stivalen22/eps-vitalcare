import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { HeartPulse, LogIn } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { getErrorMessage } from '../api/client'
import { Field, Notice } from '../components/ui'
import { isEmail } from '../utils/format'

export default function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [form, setForm] = useState({ email: '', password: '' })
  const [errors, setErrors] = useState({})
  const [serverError, setServerError] = useState('')
  const [loading, setLoading] = useState(false)

  const onChange = (e) => setForm({ ...form, [e.target.name]: e.target.value })

  const onSubmit = async (e) => {
    e.preventDefault()
    const errs = {}
    if (!isEmail(form.email)) errs.email = 'Ingrese un correo válido'
    if (!form.password) errs.password = 'Ingrese su contraseña'
    setErrors(errs)
    if (Object.keys(errs).length) return

    setLoading(true)
    setServerError('')
    try {
      await login(form.email.trim(), form.password)
      navigate(location.state?.from?.pathname || '/', { replace: true })
    } catch (err) {
      setServerError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-card card">
        <div className="auth-brand">
          <HeartPulse size={36} aria-hidden="true" />
          <div>
            <h1>EPS VitalCare</h1>
            <p className="muted">Gestión de citas y servicios de salud</p>
          </div>
        </div>
        <form onSubmit={onSubmit} noValidate>
          {serverError && <Notice tone="danger">{serverError}</Notice>}
          <Field label="Correo electrónico" error={errors.email} required>
            <input name="email" type="email" autoComplete="username" value={form.email} onChange={onChange} />
          </Field>
          <Field label="Contraseña" error={errors.password} required>
            <input
              name="password"
              type="password"
              autoComplete="current-password"
              value={form.password}
              onChange={onChange}
            />
          </Field>
          <button className="btn btn-primary btn-block" disabled={loading}>
            <LogIn size={18} /> {loading ? 'Ingresando...' : 'Iniciar sesión'}
          </button>
        </form>
        <p className="auth-footer">
          ¿Eres paciente nuevo? <Link to="/registro">Crea tu cuenta</Link>
        </p>
        <p className="disclaimer">
          Prototipo académico. No representa una EPS real ni está conectado a entidades oficiales.
        </p>
      </div>
    </div>
  )
}
