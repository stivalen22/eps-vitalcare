/** Panel principal: cambia según el rol. Todas las cifras vienen de /dashboard/stats. */
import { Link } from 'react-router-dom'
import {
  Bell,
  CalendarCheck,
  CalendarClock,
  CalendarPlus,
  ClipboardList,
  FileClock,
  History,
  Stethoscope,
  Users,
} from 'lucide-react'
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { useAuth } from '../context/AuthContext'
import { useFetch } from '../hooks/useFetch'
import { dashboardApi } from '../api/services'
import { ErrorState, Loader, PageHeader, StatCard } from '../components/ui'
import AppointmentList from '../components/AppointmentList'
import { DataTable } from '../components/DataTable'
import { AppointmentBadge } from '../components/ui'
import { APPOINTMENT_STATUS, formatDate, formatDateLong, formatTime } from '../utils/format'

const CHART_COLOR = '#1559c7'

export default function DashboardPage() {
  const { user } = useAuth()
  const { data, loading, error, reload } = useFetch(() => dashboardApi.stats(), [])

  const greeting = `Hola, ${user.nombre_completo.split(' ')[0]}`
  if (loading) return <Loader text="Cargando panel..." />
  if (error) return <ErrorState message={error} onRetry={reload} />

  const stats = data.data
  if (user.rol === 'admin') return <AdminDashboard stats={stats} />
  if (user.rol === 'medico') return <DoctorDashboard stats={stats} greeting={greeting} />
  return <PatientDashboard stats={stats} greeting={greeting} />
}

function PatientDashboard({ stats, greeting }) {
  const next = stats.proxima_cita
  return (
    <>
      <PageHeader
        title={greeting}
        subtitle="Resumen de tus citas y solicitudes"
        actions={
          <>
            <Link to="/citas/nueva" className="btn btn-primary">
              <CalendarPlus size={18} /> Solicitar cita
            </Link>
            <Link to="/historial" className="btn btn-secondary">
              <History size={18} /> Ver historial
            </Link>
          </>
        }
      />
      <div className="card next-appt">
        <h2>Próxima cita</h2>
        {next ? (
          <Link to={`/citas/${next.id}`} className="next-appt-body">
            <CalendarClock size={40} aria-hidden="true" />
            <div>
              <p className="next-appt-date">
                {formatDateLong(next.fecha)} · {formatTime(next.hora_inicio)}
              </p>
              <p>
                {next.servicio_nombre} con {next.medico_nombre}
              </p>
            </div>
            <AppointmentBadge estado={next.estado} />
          </Link>
        ) : (
          <p className="muted">No tienes citas programadas. Puedes solicitar una cuando lo necesites.</p>
        )}
      </div>
      <div className="stats-grid">
        <StatCard icon={ClipboardList} label="Total de citas" value={stats.total_citas} />
        <StatCard icon={CalendarCheck} label="Citas pendientes" value={stats.citas_pendientes} tone="warning" />
        <StatCard
          icon={FileClock}
          label="Autorizaciones en trámite"
          value={stats.autorizaciones_en_tramite}
          tone="info"
        />
        <StatCard icon={Bell} label="Notificaciones sin leer" value={stats.notificaciones_no_leidas} tone="neutral" />
      </div>
    </>
  )
}

function DoctorDashboard({ stats, greeting }) {
  return (
    <>
      <PageHeader
        title={greeting}
        subtitle="Tu agenda de hoy y próximas citas"
        actions={
          <Link to="/agenda" className="btn btn-primary">
            <CalendarClock size={18} /> Abrir agenda
          </Link>
        }
      />
      <div className="stats-grid">
        <StatCard icon={CalendarCheck} label="Citas de hoy" value={stats.citas_hoy} />
        <StatCard icon={ClipboardList} label="Pendientes de atención" value={stats.pendientes_atencion} tone="warning" />
        <StatCard icon={CalendarClock} label="Próximas citas" value={stats.proximas_citas.length} tone="info" />
        <StatCard icon={Bell} label="Notificaciones sin leer" value={stats.notificaciones_no_leidas} tone="neutral" />
      </div>
      <div className="grid-2">
        <section className="card">
          <h2>Agenda de hoy</h2>
          <AppointmentList items={stats.agenda_hoy} show="paciente" emptyText="Sin citas para hoy" />
        </section>
        <section className="card">
          <h2>Próximas citas</h2>
          <AppointmentList items={stats.proximas_citas} show="paciente" emptyText="Sin citas próximas" />
        </section>
      </div>
    </>
  )
}

function AdminDashboard({ stats }) {
  const byStatus = stats.citas_por_estado.map((r) => ({
    estado: APPOINTMENT_STATUS[r.estado]?.label || r.estado,
    total: r.total,
  }))
  const columns = [
    { key: 'fecha', header: 'Fecha', render: (c) => `${formatDate(c.fecha)} ${formatTime(c.hora_inicio)}` },
    { key: 'paciente_nombre', header: 'Paciente' },
    { key: 'medico_nombre', header: 'Médico' },
    { key: 'servicio_nombre', header: 'Servicio' },
    { key: 'estado', header: 'Estado', render: (c) => <AppointmentBadge estado={c.estado} /> },
    {
      key: 'ver',
      header: '',
      render: (c) => (
        <Link className="btn btn-ghost btn-sm" to={`/citas/${c.id}`}>
          Ver
        </Link>
      ),
    },
  ]
  return (
    <>
      <PageHeader title="Panel administrativo" subtitle="Indicadores calculados desde la base de datos" />
      <div className="stats-grid stats-grid-5">
        <StatCard icon={Users} label="Pacientes activos" value={stats.pacientes_activos} />
        <StatCard icon={Stethoscope} label="Médicos activos" value={stats.medicos_activos} tone="info" />
        <StatCard icon={CalendarCheck} label="Citas de hoy" value={stats.citas_hoy} tone="primary" />
        <StatCard icon={ClipboardList} label="Citas pendientes" value={stats.citas_pendientes} tone="warning" />
        <StatCard
          icon={FileClock}
          label="Autorizaciones por revisar"
          value={stats.autorizaciones_pendientes}
          tone="neutral"
        />
      </div>
      <div className="grid-2">
        <section className="card">
          <h2>Citas por estado</h2>
          <ChartBox data={byStatus} xKey="estado" label="Citas" />
        </section>
        <section className="card">
          <h2>Citas por mes (últimos 6 meses)</h2>
          <ChartBox data={stats.citas_por_mes} xKey="periodo" label="Citas" />
        </section>
      </div>
      <section className="card">
        <h2>Citas recientes</h2>
        <DataTable columns={columns} rows={stats.citas_recientes} emptyTitle="Aún no hay citas registradas" />
      </section>
    </>
  )
}

/** Gráfica de barras de una sola serie (un solo color: la etiqueta del eje identifica cada barra). */
function ChartBox({ data, xKey, label }) {
  return (
    <div className="chart-box">
      <ResponsiveContainer width="100%" height={240}>
        <BarChart data={data} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
          <CartesianGrid vertical={false} stroke="#e5e9f0" />
          <XAxis dataKey={xKey} tick={{ fontSize: 12, fill: '#5b6576' }} tickLine={false} axisLine={false} />
          <YAxis allowDecimals={false} tick={{ fontSize: 12, fill: '#5b6576' }} tickLine={false} axisLine={false} />
          <Tooltip cursor={{ fill: 'rgba(21,89,199,0.06)' }} formatter={(v) => [v, label]} />
          <Bar dataKey="total" name={label} fill={CHART_COLOR} radius={[4, 4, 0, 0]} maxBarSize={36} />
        </BarChart>
      </ResponsiveContainer>
      {/* Tabla accesible equivalente a la gráfica */}
      <table className="sr-only">
        <caption>{label}</caption>
        <tbody>
          {data.map((d) => (
            <tr key={d[xKey]}>
              <th>{d[xKey]}</th>
              <td>{d.total}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
