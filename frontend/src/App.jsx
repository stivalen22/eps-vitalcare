import { Route, Routes } from 'react-router-dom'
import AppLayout from './layouts/AppLayout'
import { ProtectedRoute, PublicOnlyRoute } from './routes/ProtectedRoute'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import DashboardPage from './pages/DashboardPage'
import ProfilePage from './pages/ProfilePage'
import PatientsPage from './pages/PatientsPage'
import DoctorsPage from './pages/DoctorsPage'
import SpecialtiesPage from './pages/SpecialtiesPage'
import ServicesPage from './pages/ServicesPage'
import SchedulesPage from './pages/SchedulesPage'
import AppointmentsPage from './pages/AppointmentsPage'
import NewAppointmentPage from './pages/NewAppointmentPage'
import AppointmentDetailPage from './pages/AppointmentDetailPage'
import AgendaPage from './pages/AgendaPage'
import HistoryPage from './pages/HistoryPage'
import AuthorizationsPage from './pages/AuthorizationsPage'
import NotificationsPage from './pages/NotificationsPage'
import UsersPage from './pages/UsersPage'
import AuditPage from './pages/AuditPage'
import NotFoundPage from './pages/NotFoundPage'

export default function App() {
  return (
    <Routes>
      <Route element={<PublicOnlyRoute />}>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/registro" element={<RegisterPage />} />
      </Route>

      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
          <Route index element={<DashboardPage />} />
          <Route path="perfil" element={<ProfilePage />} />
          <Route path="notificaciones" element={<NotificationsPage />} />
          <Route path="citas" element={<AppointmentsPage />} />
          <Route path="citas/:id" element={<AppointmentDetailPage />} />
          <Route path="servicios" element={<ServicesPage />} />

          <Route element={<ProtectedRoute roles={['paciente', 'admin']} />}>
            <Route path="citas/nueva" element={<NewAppointmentPage />} />
            <Route path="autorizaciones" element={<AuthorizationsPage />} />
            <Route path="medicos" element={<DoctorsPage />} />
          </Route>
          <Route element={<ProtectedRoute roles={['paciente', 'medico']} />}>
            <Route path="historial" element={<HistoryPage />} />
          </Route>
          <Route element={<ProtectedRoute roles={['medico', 'admin']} />}>
            <Route path="agenda" element={<AgendaPage />} />
            <Route path="horarios" element={<SchedulesPage />} />
          </Route>
          <Route element={<ProtectedRoute roles={['admin']} />}>
            <Route path="pacientes" element={<PatientsPage />} />
            <Route path="especialidades" element={<SpecialtiesPage />} />
            <Route path="usuarios" element={<UsersPage />} />
            <Route path="auditoria" element={<AuditPage />} />
          </Route>
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Route>
    </Routes>
  )
}
