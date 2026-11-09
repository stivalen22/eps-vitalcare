/** Estructura principal: barra lateral, barra superior y contenido. */
import { useEffect, useState } from 'react'
import { Link, NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { Bell, HeartPulse, LogOut, Menu, X } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { navFor } from '../routes/navigation'
import { ROLE_LABELS } from '../utils/format'
import { notificationsApi } from '../api/services'

export default function AppLayout() {
  const { user, logout } = useAuth()
  const [open, setOpen] = useState(false)
  const [unread, setUnread] = useState(0)
  const location = useLocation()
  const navigate = useNavigate()

  // Cierra el menú móvil al navegar y actualiza el contador de notificaciones
  useEffect(() => {
    setOpen(false)
    notificationsApi
      .list({ solo_no_leidas: true, size: 1 })
      .then((r) => setUnread(r.total))
      .catch(() => setUnread(0))
  }, [location.pathname])

  const handleLogout = () => {
    logout()
    navigate('/login', { replace: true })
  }

  const initials = user.nombre_completo
    .split(' ')
    .slice(0, 2)
    .map((p) => p[0])
    .join('')
    .toUpperCase()

  return (
    <div className={`app-shell ${open ? 'nav-open' : ''}`}>
      <aside className="sidebar" aria-label="Navegación principal">
        <div className="brand">
          <HeartPulse size={26} aria-hidden="true" />
          <span>
            EPS <strong>VitalCare</strong>
          </span>
          <button className="icon-btn sidebar-close" onClick={() => setOpen(false)} aria-label="Cerrar menú">
            <X size={20} />
          </button>
        </div>
        <nav>
          {navFor(user.rol).map(({ to, label, icon: Icon }) => (
            <NavLink key={to} to={to} end={to === '/' || to === '/citas'} className="nav-link">
              <Icon size={18} aria-hidden="true" />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>
        <p className="sidebar-note">Prototipo académico · datos ficticios</p>
      </aside>
      {open && <div className="sidebar-backdrop" onClick={() => setOpen(false)} />}

      <div className="main">
        <header className="topbar">
          <button className="icon-btn menu-btn" onClick={() => setOpen(true)} aria-label="Abrir menú">
            <Menu size={22} />
          </button>
          <Link to="/" className="topbar-title">
            EPS VitalCare
          </Link>
          <div className="topbar-right">
            <Link to="/notificaciones" className="icon-btn notif-btn" aria-label={`Notificaciones (${unread} sin leer)`}>
              <Bell size={20} />
              {unread > 0 && <span className="notif-dot">{unread > 9 ? '9+' : unread}</span>}
            </Link>
            <div className="user-chip">
              <span className="avatar" aria-hidden="true">
                {initials}
              </span>
              <span className="user-info">
                <strong>{user.nombre_completo}</strong>
                <small>{ROLE_LABELS[user.rol]}</small>
              </span>
            </div>
            <button className="btn btn-ghost" onClick={handleLogout}>
              <LogOut size={18} /> <span className="hide-sm">Salir</span>
            </button>
          </div>
        </header>
        <main className="content">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
