import { Link } from 'react-router-dom'
import { SearchX } from 'lucide-react'

export default function NotFoundPage() {
  return (
    <div className="status-page">
      <SearchX size={48} aria-hidden="true" />
      <h1>Página no encontrada</h1>
      <p className="muted">La dirección que buscas no existe o fue movida.</p>
      <Link to="/" className="btn btn-primary">
        Ir al panel
      </Link>
    </div>
  )
}
