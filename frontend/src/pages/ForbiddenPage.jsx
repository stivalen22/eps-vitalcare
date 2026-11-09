import { Link } from 'react-router-dom'
import { ShieldAlert } from 'lucide-react'

export default function ForbiddenPage() {
  return (
    <div className="status-page">
      <ShieldAlert size={48} aria-hidden="true" />
      <h1>Acceso restringido</h1>
      <p className="muted">Tu rol no tiene permisos para ver esta sección.</p>
      <Link to="/" className="btn btn-primary">
        Volver al panel
      </Link>
    </div>
  )
}
