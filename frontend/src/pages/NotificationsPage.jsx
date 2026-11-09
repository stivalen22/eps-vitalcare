import { useState } from 'react'
import { Bell, CheckCheck } from 'lucide-react'
import { notificationsApi } from '../api/services'
import { getErrorMessage } from '../api/client'
import { useToast } from '../context/ToastContext'
import { useFetch } from '../hooks/useFetch'
import { Pagination } from '../components/DataTable'
import { EmptyState, ErrorState, Loader, PageHeader } from '../components/ui'
import { formatDateTime } from '../utils/format'

export default function NotificationsPage() {
  const toast = useToast()
  const [page, setPage] = useState(1)
  const [onlyUnread, setOnlyUnread] = useState(false)
  const { data, loading, error, reload, setData } = useFetch(
    () => notificationsApi.list({ page, size: 15, solo_no_leidas: onlyUnread }),
    [page, onlyUnread],
  )

  const markRead = async (n) => {
    try {
      const updated = await notificationsApi.markRead(n.id)
      setData((d) => ({ ...d, items: d.items.map((x) => (x.id === n.id ? updated : x)) }))
    } catch (err) {
      toast.error(getErrorMessage(err))
    }
  }

  const markAll = async () => {
    try {
      const res = await notificationsApi.markAllRead()
      toast.success(res.detail)
      reload()
    } catch (err) {
      toast.error(getErrorMessage(err))
    }
  }

  return (
    <>
      <PageHeader
        title="Notificaciones"
        subtitle="Avisos internos del sistema (no se envían correos ni SMS)"
        actions={
          <button className="btn btn-secondary" onClick={markAll}>
            <CheckCheck size={18} /> Marcar todas como leídas
          </button>
        }
      />
      <div className="card">
        <label className="checkbox">
          <input
            type="checkbox"
            checked={onlyUnread}
            onChange={(e) => {
              setOnlyUnread(e.target.checked)
              setPage(1)
            }}
          />
          Mostrar solo no leídas
        </label>
        {loading ? (
          <Loader />
        ) : error ? (
          <ErrorState message={error} onRetry={reload} />
        ) : !data.items.length ? (
          <EmptyState title="No tienes notificaciones" />
        ) : (
          <ul className="notif-list">
            {data.items.map((n) => (
              <li key={n.id} className={n.leida ? 'read' : 'unread'}>
                <Bell size={18} aria-hidden="true" />
                <div>
                  <strong>{n.titulo}</strong>
                  <p>{n.mensaje}</p>
                  <small className="muted">{formatDateTime(n.creado_en)}</small>
                </div>
                {!n.leida && (
                  <button className="btn btn-ghost btn-sm" onClick={() => markRead(n)}>
                    Marcar leída
                  </button>
                )}
              </li>
            ))}
          </ul>
        )}
        {data && <Pagination page={page} size={15} total={data.total} onChange={setPage} />}
      </div>
    </>
  )
}
