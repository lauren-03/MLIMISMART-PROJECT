// Admin: read-only view of the database tables.
import { useCallback, useEffect, useState } from 'react'

import { api, errorMessage } from '../api/client'
import { ErrorBox, Spinner } from '../components/Shared'
import { useApp } from '../context/AppContext'

const SIZE = 25

function cell(value) {
  if (value === null || value === undefined) return '—'
  if (typeof value === 'boolean') return value ? 'yes' : 'no'
  return String(value)
}

export default function DatabasePanel() {
  const { t } = useApp()
  const [tables, setTables] = useState(null)
  const [active, setActive] = useState(null)
  const [data, setData] = useState(null)
  const [page, setPage] = useState(1)
  const [query, setQuery] = useState('')
  const [search, setSearch] = useState('')
  const [selected, setSelected] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const loadTables = useCallback(() => {
    api.get('/admin/db/tables')
      .then(({ data: body }) => {
        setTables(body)
        setActive((current) => current ?? body.find((x) => x.name === 'farmers')?.name ?? body[0]?.name)
      })
      .catch((err) => setError(errorMessage(err, t('errorGeneric')) ?? 'network'))
  }, [t])

  useEffect(() => {
    loadTables()
  }, [loadTables])

  useEffect(() => {
    if (!active) return
    let cancelled = false
    setLoading(true)
    setSelected(null)
    api.get(`/admin/db/tables/${active}`, { params: { page, size: SIZE, q: search } })
      .then(({ data: body }) => !cancelled && setData(body))
      .catch((err) => !cancelled && setError(errorMessage(err, t('errorGeneric')) ?? 'network'))
      .finally(() => !cancelled && setLoading(false))
    return () => {
      cancelled = true
    }
  }, [active, page, search, t])

  const choose = (name) => {
    setActive(name)
    setPage(1)
    setQuery('')
    setSearch('')
  }

  const submitSearch = (event) => {
    event.preventDefault()
    setPage(1)
    setSearch(query.trim())
  }

  const pages = data ? Math.max(1, Math.ceil(data.total / data.size)) : 1

  return (
    <div className="row g-4">
      <div className="col-lg-3">
        <div className="card card-mlimi">
          <div className="card-body p-2">
            <div className="d-flex justify-content-between align-items-center px-2 pt-1 pb-2">
              <h2 className="h6 mb-0">{t('dbTables')}</h2>
              <button type="button" className="btn btn-sm btn-link text-tea p-0" onClick={loadTables}>
                {t('dbRefresh')}
              </button>
            </div>
            {!tables && <Spinner />}
            {tables?.map((table) => (
              <button
                type="button"
                key={table.name}
                className={`area-row${active === table.name ? ' selected' : ''}`}
                onClick={() => choose(table.name)}
                aria-pressed={active === table.name}
              >
                <span className="fw-semibold small">{table.name}</span>
                <span className="badge bg-light text-tea border">{table.rows}</span>
              </button>
            ))}
          </div>
        </div>
        <p className="small text-muted mt-2">{t('dbReadOnly')}</p>
      </div>

      <div className="col-lg-9">
        <ErrorBox error={error} />
        {data && (
          <div className="card card-mlimi">
            <div className="card-body">
              <div className="d-flex justify-content-between align-items-start flex-wrap gap-2 mb-3">
                <div>
                  <h2 className="h5 text-tea mb-0">{data.table}</h2>
                  <div className="small text-muted">
                    {data.description} · {data.total} {t('dbRows')}
                    {data.hidden.length > 0 && ` · ${t('dbHidden')}: ${data.hidden.join(', ')}`}
                  </div>
                </div>
                <form className="d-flex gap-2" onSubmit={submitSearch} role="search">
                  <label className="visually-hidden" htmlFor="db-search">{t('dbSearch')}</label>
                  <input id="db-search" className="form-control form-control-sm" placeholder={t('dbSearch')}
                         value={query} onChange={(e) => setQuery(e.target.value)} style={{ minWidth: 180 }} />
                  <button className="btn btn-sm btn-tea">{t('dbSearchButton')}</button>
                  {search && (
                    <button type="button" className="btn btn-sm btn-outline-tea"
                            onClick={() => { setQuery(''); setSearch(''); setPage(1) }}>
                      {t('dbClear')}
                    </button>
                  )}
                </form>
              </div>

              {loading ? <Spinner /> : (
                <div className="table-responsive db-table">
                  <table className="table table-sm table-hover align-middle mb-0">
                    <thead>
                      <tr>{data.columns.map((c) => <th scope="col" key={c}>{c}</th>)}</tr>
                    </thead>
                    <tbody>
                      {data.rows.length === 0 && (
                        <tr><td colSpan={data.columns.length} className="text-muted">{t('dbEmpty')}</td></tr>
                      )}
                      {data.rows.map((row, i) => (
                        <tr key={i} onClick={() => setSelected(selected === i ? null : i)}
                            className={selected === i ? 'table-active' : ''} style={{ cursor: 'pointer' }}>
                          {row.map((value, j) => (
                            <td key={j} title={cell(value)}>{cell(value)}</td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {selected !== null && data.rows[selected] && (
                <dl className="db-detail mt-3">
                  {data.columns.map((c, j) => (
                    <div key={c}>
                      <dt>{c}</dt>
                      <dd>{cell(data.rows[selected][j])}</dd>
                    </div>
                  ))}
                </dl>
              )}

              <div className="d-flex justify-content-between align-items-center mt-3">
                <span className="small text-muted">
                  {t('dbPage')} {data.page} / {pages}
                </span>
                <div className="d-flex gap-2">
                  <button type="button" className="btn btn-sm btn-outline-tea" disabled={page <= 1}
                          onClick={() => setPage((p) => p - 1)}>{t('dbPrev')}</button>
                  <button type="button" className="btn btn-sm btn-outline-tea" disabled={page >= pages}
                          onClick={() => setPage((p) => p + 1)}>{t('dbNext')}</button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
