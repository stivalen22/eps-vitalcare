/** Administración de usuarios y roles (operaciones protegidas en el backend). */
import { useState } from 'react'
import { Power, ShieldCheck } from 'lucide-react'
import { usersApi } from '../api/services'
import { getErrorMessage } from '../api/client'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import { useFetch } from '../hooks/useFetch'
import { useListState } from '../hooks/useListState'
import { DataTable, Pagination } from '../components/DataTable'
import { ConfirmDialog } from '../components/Modal'
import { ActiveBadge, Badge, Field, PageHeader, SearchInput } from '../components/ui'
import { ROLE_LABELS, formatDateTime } from '../utils/format'

export default function UsersPage() {
  const { user: me } = useAuth()
  const toast = useToast()
  const list = useListState({ rol: '', activo: '' })
  const { data, loading, error, reload } = useFetch(() => usersApi.list(list.params), [list.paramsKey])
  const [roleChange, setRoleChange] = useState(null) // { user, rol }
  const [toggle, setToggle] = useState(null)
  const [busy, setBusy] = useState(false)

  const run = async (fn, msg) => {
    setBusy(true)
    try {
      await fn()
      toast.success(msg)
      reload()
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setBusy(false)
      setRoleChange(null)
      setToggle(null)
    }
  }

  const columns = [
    { key: 'nombre_completo', header: 'Nombre' },
    { key: 'email', header: 'Correo' },
    { key: 'rol', header: 'Rol', render: (u) => <Badge tone="info">{ROLE_LABELS[u.rol]}</Badge> },
    { key: 'activo', header: 'Estado', render: (u) => <ActiveBadge activo={u.activo} /> },
    { key: 'creado_en', header: 'Creado', render: (u) => formatDateTime(u.creado_en) },
    {
      key: 'acciones',
      header: 'Acciones',
      className: 'actions',
      render: (u) =>
        u.id === me.id ? (
          <small className="muted">Tu cuenta</small>
        ) : (
          <div className="row-actions">
            <button
              className="icon-btn"
              title="Cambiar rol"
              aria-label="Cambiar rol"
              onClick={() => setRoleChange({ user: u, rol: u.rol })}
            >
              <ShieldCheck size={17} />
            </button>
            <button
              className={`icon-btn ${u.activo ? 'danger' : 'success'}`}
              title={u.activo ? 'Desactivar' : 'Activar'}
              aria-label={u.activo ? 'Desactivar' : 'Activar'}
              onClick={() => setToggle(u)}
            >
              <Power size={17} />
            </button>
          </div>
        ),
    },
  ]

  return (
    <>
      <PageHeader title="Usuarios y roles" subtitle="Las contraseñas nunca se muestran: solo se almacenan como hash" />
      <div className="card">
        <div className="toolbar">
          <SearchInput value={list.search} onChange={list.setSearch} placeholder="Buscar por nombre o correo" />
          <select value={list.filters.rol} onChange={(e) => list.setFilter('rol', e.target.value)} aria-label="Rol">
            <option value="">Todos los roles</option>
            {Object.entries(ROLE_LABELS).map(([k, v]) => (
              <option key={k} value={k}>
                {v}
              </option>
            ))}
          </select>
          <select value={list.filters.activo} onChange={(e) => list.setFilter('activo', e.target.value)} aria-label="Estado">
            <option value="">Todos los estados</option>
            <option value="true">Activos</option>
            <option value="false">Inactivos</option>
          </select>
        </div>
        <DataTable columns={columns} rows={data?.items} loading={loading} error={error} onRetry={reload} />
        {data && <Pagination page={list.page} size={list.size} total={data.total} onChange={list.setPage} />}
      </div>

      <ConfirmDialog
        open={!!roleChange}
        title="Cambiar rol"
        confirmText="Guardar rol"
        loading={busy}
        onConfirm={() => run(() => usersApi.setRole(roleChange.user.id, roleChange.rol), 'Rol actualizado')}
        onCancel={() => setRoleChange(null)}
      >
        {roleChange && (
          <>
            <p>
              Usuario: <strong>{roleChange.user.email}</strong>
            </p>
            <Field label="Nuevo rol" hint="El rol debe coincidir con el perfil de la cuenta (paciente o médico)">
              <select value={roleChange.rol} onChange={(e) => setRoleChange({ ...roleChange, rol: e.target.value })}>
                {Object.entries(ROLE_LABELS).map(([k, v]) => (
                  <option key={k} value={k}>
                    {v}
                  </option>
                ))}
              </select>
            </Field>
          </>
        )}
      </ConfirmDialog>

      <ConfirmDialog
        open={!!toggle}
        danger={toggle?.activo}
        title={toggle?.activo ? 'Desactivar cuenta' : 'Activar cuenta'}
        message={toggle?.activo ? 'El usuario no podrá iniciar sesión.' : 'El usuario podrá volver a iniciar sesión.'}
        confirmText={toggle?.activo ? 'Desactivar' : 'Activar'}
        loading={busy}
        onConfirm={() =>
          run(() => usersApi.setStatus(toggle.id, !toggle.activo), toggle.activo ? 'Cuenta desactivada' : 'Cuenta activada')
        }
        onCancel={() => setToggle(null)}
      />
    </>
  )
}
