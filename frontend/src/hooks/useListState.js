/**
 * Estado común de los listados: búsqueda (con retraso), filtros y página.
 * Al cambiar un filtro se vuelve a la página 1.
 */
import { useState } from 'react'
import { useDebounce } from './useFetch'

export function useListState(initialFilters = {}, size = 10) {
  const [search, setSearchRaw] = useState('')
  const [filters, setFiltersRaw] = useState(initialFilters)
  const [page, setPage] = useState(1)
  const q = useDebounce(search)

  const setSearch = (value) => {
    setSearchRaw(value)
    setPage(1)
  }
  const setFilter = (key, value) => {
    setFiltersRaw((f) => ({ ...f, [key]: value }))
    setPage(1)
  }

  const params = { q, ...filters, page, size }
  return { search, setSearch, filters, setFilter, page, setPage, size, params, paramsKey: JSON.stringify(params) }
}
