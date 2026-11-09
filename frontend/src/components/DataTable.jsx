/**
 * Tabla reutilizable con estados de carga, error, vacío y paginación.
 * columns: [{ key, header, render?: (row) => node, className? }]
 * En pantallas pequeñas cada fila se muestra como tarjeta (ver styles).
 */
import { ChevronLeft, ChevronRight } from 'lucide-react'
import { EmptyState, ErrorState, Loader } from './ui'

export function DataTable({ columns, rows, loading, error, onRetry, emptyTitle, emptyMessage, rowKey = 'id' }) {
  if (loading) return <Loader />
  if (error) return <ErrorState message={error} onRetry={onRetry} />
  if (!rows || rows.length === 0) return <EmptyState title={emptyTitle} message={emptyMessage} />

  return (
    <div className="table-wrap">
      <table className="table">
        <thead>
          <tr>
            {columns.map((c) => (
              <th key={c.key} className={c.className}>
                {c.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row[rowKey]}>
              {columns.map((c) => (
                <td key={c.key} className={c.className} data-label={c.header}>
                  {c.render ? c.render(row) : row[c.key] ?? '—'}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export function Pagination({ page, size, total, onChange }) {
  const pages = Math.max(1, Math.ceil(total / size))
  if (total <= size) return total ? <p className="pagination-info">{total} registro(s)</p> : null
  return (
    <div className="pagination">
      <span className="pagination-info">
        Página {page} de {pages} · {total} registros
      </span>
      <div className="pagination-buttons">
        <button className="btn btn-secondary btn-sm" disabled={page <= 1} onClick={() => onChange(page - 1)}>
          <ChevronLeft size={16} /> Anterior
        </button>
        <button className="btn btn-secondary btn-sm" disabled={page >= pages} onClick={() => onChange(page + 1)}>
          Siguiente <ChevronRight size={16} />
        </button>
      </div>
    </div>
  )
}
