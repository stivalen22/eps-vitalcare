import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { HeartPulse, UserPlus } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import { getErrorMessage } from '../api/client'
import { Notice } from '../components/ui'
import { EMPTY_PATIENT, PatientFormFields, toPatientPayload, validatePatient } from '../components/PatientFormFields'

export default function RegisterPage() {
  const { register } = useAuth()
  const toast = useToast()
  const navigate = useNavigate()
  const [form, setForm] = useState(EMPTY_PATIENT)
  const [errors, setErrors] = useState({})
  const [serverError, setServerError] = useState('')
  const [loading, setLoading] = useState(false)

  const onChange = (e) => setForm({ ...form, [e.target.name]: e.target.value })

  const onSubmit = async (e) => {
    e.preventDefault()
    const errs = validatePatient(form)
    setErrors(errs)
    if (Object.keys(errs).length) return
    setLoading(true)
    setServerError('')
    try {
      await register(toPatientPayload(form))
      toast.success('Cuenta creada correctamente. ¡Bienvenido!')
      navigate('/', { replace: true })
    } catch (err) {
      setServerError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-card auth-card-wide card">
        <div className="auth-brand">
          <HeartPulse size={36} aria-hidden="true" />
          <div>
            <h1>Registro de paciente</h1>
            <p className="muted">Crea tu cuenta en EPS VitalCare</p>
          </div>
        </div>
        <form onSubmit={onSubmit} noValidate>
          {serverError && <Notice tone="danger">{serverError}</Notice>}
          <Notice tone="info">Este es un prototipo académico: utiliza únicamente datos ficticios.</Notice>
          <PatientFormFields form={form} errors={errors} onChange={onChange} />
          <button className="btn btn-primary btn-block" disabled={loading}>
            <UserPlus size={18} /> {loading ? 'Creando cuenta...' : 'Crear cuenta'}
          </button>
        </form>
        <p className="auth-footer">
          ¿Ya tienes cuenta? <Link to="/login">Inicia sesión</Link>
        </p>
      </div>
    </div>
  )
}
