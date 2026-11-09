/** Menú lateral por rol. Cada rol ve solo las secciones que le corresponden. */
import {
  Bell,
  CalendarDays,
  CalendarPlus,
  ClipboardList,
  Clock,
  FileCheck2,
  History,
  LayoutDashboard,
  ScrollText,
  Stethoscope,
  Tags,
  UserCog,
  UserRound,
  Users,
  BriefcaseMedical,
} from 'lucide-react'

const NAV = {
  paciente: [
    { to: '/', label: 'Panel', icon: LayoutDashboard },
    { to: '/citas/nueva', label: 'Solicitar cita', icon: CalendarPlus },
    { to: '/citas', label: 'Mis citas', icon: CalendarDays },
    { to: '/historial', label: 'Historial', icon: History },
    { to: '/autorizaciones', label: 'Autorizaciones', icon: FileCheck2 },
    { to: '/servicios', label: 'Servicios', icon: BriefcaseMedical },
    { to: '/medicos', label: 'Médicos', icon: Stethoscope },
    { to: '/notificaciones', label: 'Notificaciones', icon: Bell },
  ],
  medico: [
    { to: '/', label: 'Panel', icon: LayoutDashboard },
    { to: '/agenda', label: 'Agenda semanal', icon: CalendarDays },
    { to: '/citas', label: 'Citas asignadas', icon: ClipboardList },
    { to: '/historial', label: 'Consultas registradas', icon: History },
    { to: '/horarios', label: 'Disponibilidad', icon: Clock },
    { to: '/notificaciones', label: 'Notificaciones', icon: Bell },
  ],
  admin: [
    { to: '/', label: 'Panel', icon: LayoutDashboard },
    { to: '/pacientes', label: 'Pacientes', icon: Users },
    { to: '/medicos', label: 'Médicos', icon: Stethoscope },
    { to: '/especialidades', label: 'Especialidades', icon: Tags },
    { to: '/servicios', label: 'Servicios', icon: BriefcaseMedical },
    { to: '/horarios', label: 'Horarios', icon: Clock },
    { to: '/citas', label: 'Citas', icon: ClipboardList },
    { to: '/agenda', label: 'Agenda', icon: CalendarDays },
    { to: '/autorizaciones', label: 'Autorizaciones', icon: FileCheck2 },
    { to: '/usuarios', label: 'Usuarios y roles', icon: UserCog },
    { to: '/auditoria', label: 'Auditoría', icon: ScrollText },
    { to: '/notificaciones', label: 'Notificaciones', icon: Bell },
  ],
}

export function navFor(rol) {
  return [...(NAV[rol] || []), { to: '/perfil', label: 'Mi perfil', icon: UserRound }]
}
