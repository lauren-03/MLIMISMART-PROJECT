// Harvest diary.
import { useCallback, useEffect, useState } from 'react'
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

import { api, errorMessage } from '../api/client'
import { ErrorBox, Footer, PageHead, Spinner, StatTile } from '../components/Shared'
import { useApp } from '../context/AppContext'

const today = () => new Date().toISOString().slice(0, 10)
const kwacha = (value) => `MK ${Math.round(value).toLocaleString('en-US')}`

function monthShort(key, language) {
  const [year, month] = key.split('-').map(Number)
  const date = new Date(year, month - 1, 1)
  return date.toLocaleString(language === 'NY' ? 'en-GB' : 'en-GB', { month: 'short' })
}

export default function Harvest() {
  const { language, t } = useApp()
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [saving, setSaving] = useState(false)
  const [form, setForm] = useState({ harvest_date: today(), kg: '', price_per_kg: '', notes: '' })

  const load = useCallback(() => {
    return api
      .get('/harvest')
      .then(({ data: body }) => {
        setData(body)
        // Pre-fill the price the farmer was last paid; it rarely changes.
        setForm((f) => (f.price_per_kg === '' && body.summary.last_price
          ? { ...f, price_per_kg: String(body.summary.last_price) } : f))
      })
      .catch((err) => setError(errorMessage(err, t('errorGeneric')) ?? 'network'))
  }, [t])

  useEffect(() => {
    load()
  }, [load])

  const submit = async (event) => {
    event.preventDefault()
    setSaving(true)
    setError(null)
    try {
      await api.post('/harvest', {
        harvest_date: form.harvest_date,
        kg: Number(form.kg),
        price_per_kg: form.price_per_kg === '' ? null : Number(form.price_per_kg),
        notes: form.notes.trim() || null,
      })
      setForm((f) => ({ ...f, kg: '', notes: '' }))
      await load()
    } catch (err) {
      setError(errorMessage(err, t('errorGeneric')) ?? 'network')
    } finally {
      setSaving(false)
    }
  }

  const remove = async (id) => {
    try {
      await api.delete(`/harvest/${id}`)
      await load()
    } catch (err) {
      setError(errorMessage(err, t('errorGeneric')) ?? 'network')
    }
  }

  const set = (key) => (event) => setForm((f) => ({ ...f, [key]: event.target.value }))
  const summary = data?.summary

  return (
    <>
      <PageHead icon="basket" title={t('harvestTitle')} intro={t('harvestIntro')} />
      <div className="container">
        <ErrorBox error={error} />

        <form className="card card-mlimi mb-4" onSubmit={submit}>
          <div className="card-body row g-3 align-items-end">
            <div className="col-6 col-md-3">
              <label htmlFor="h-date" className="form-label">{t('harvestDate')}</label>
              <input id="h-date" type="date" className="form-control" max={today()} required
                     value={form.harvest_date} onChange={set('harvest_date')} />
            </div>
            <div className="col-6 col-md-2">
              <label htmlFor="h-kg" className="form-label">{t('harvestKg')}</label>
              <input id="h-kg" type="number" className="form-control" min="0.1" max="5000" step="0.1"
                     required inputMode="decimal" value={form.kg} onChange={set('kg')} />
            </div>
            <div className="col-6 col-md-2">
              <label htmlFor="h-price" className="form-label">{t('harvestPrice')}</label>
              <input id="h-price" type="number" className="form-control" min="0" step="1"
                     inputMode="numeric" placeholder="250" value={form.price_per_kg}
                     onChange={set('price_per_kg')} />
            </div>
            <div className="col-6 col-md-3">
              <label htmlFor="h-notes" className="form-label">
                {t('harvestNotes')} <span className="text-muted fw-normal">({t('optional')})</span>
              </label>
              <input id="h-notes" type="text" className="form-control" maxLength={255}
                     value={form.notes} onChange={set('notes')} />
            </div>
            <div className="col-12 col-md-2 d-grid">
              <button className="btn btn-tea" disabled={saving}>
                {t('harvestAdd')}
              </button>
            </div>
            {form.kg && form.price_per_kg && (
              <div className="col-12 small text-muted">
                = <strong className="text-tea">{kwacha(Number(form.kg) * Number(form.price_per_kg))}</strong>
              </div>
            )}
          </div>
        </form>

        {!data && !error && <Spinner />}

        {summary && (
          <>
            <div className="row g-3 mb-4">
              <div className="col-6 col-lg-3">
                <StatTile icon="basket" figure={`${summary.total_kg.toLocaleString()} kg`} caption={t('harvestTotalKg')} />
              </div>
              <div className="col-6 col-lg-3">
                <StatTile icon="cash-coin" figure={kwacha(summary.total_income)} caption={t('harvestIncome')} />
              </div>
              <div className="col-6 col-lg-3">
                <StatTile icon="calendar-check" figure={`${summary.this_month_kg} kg`} caption={t('harvestMonth')} />
              </div>
              <div className="col-6 col-lg-3">
                <StatTile
                  icon="arrow-repeat"
                  figure={summary.rounds}
                  caption={summary.kg_per_ha ? `${t('harvestRounds')} · ${summary.kg_per_ha} ${t('harvestPerHa')}` : t('harvestRounds')}
                />
              </div>
            </div>

            <div className="row g-4">
              <div className="col-lg-7">
                <div className="card card-mlimi h-100">
                  <div className="card-body">
                    <h2 className="h6 text-uppercase text-muted mb-3">{t('harvestChart')} (kg)</h2>
                    <div style={{ height: 300 }}>
                      <ResponsiveContainer>
                        <BarChart data={data.monthly.map((m) => ({ ...m, label: monthShort(m.month, language) }))}
                                  margin={{ top: 8, right: 8, left: -12, bottom: 0 }}>
                          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#dbe8de" />
                          <XAxis dataKey="label" tick={{ fontSize: 12 }} />
                          <YAxis tick={{ fontSize: 12 }} />
                          <Tooltip
                            formatter={(value, name, item) => [`${value} kg · ${kwacha(item.payload.income)}`, '']}
                            labelStyle={{ fontWeight: 700 }}
                          />
                          <Bar dataKey="kg" fill="#2e9c4f" radius={[6, 6, 0, 0]} />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                </div>
              </div>
              <div className="col-lg-5">
                <div className="card card-mlimi h-100">
                  <div className="card-body">
                    {data.records.length === 0 ? (
                      <p className="text-muted mb-0">{t('harvestEmpty')}</p>
                    ) : (
                      <div className="table-responsive" style={{ maxHeight: 330 }}>
                        <table className="table table-hover align-middle mb-0">
                          <thead>
                            <tr>
                              <th scope="col">{t('harvestDate')}</th>
                              <th scope="col" className="text-end">kg</th>
                              <th scope="col" className="text-end">{t('harvestIncomeCol')}</th>
                              <th scope="col"><span className="visually-hidden">{t('harvestDelete')}</span></th>
                            </tr>
                          </thead>
                          <tbody>
                            {data.records.map((row) => (
                              <tr key={row.id}>
                                <td>
                                  {row.harvest_date}
                                  {row.notes && <div className="small text-muted">{row.notes}</div>}
                                </td>
                                <td className="text-end">{row.kg}</td>
                                <td className="text-end">{row.income !== null ? Math.round(row.income).toLocaleString() : '—'}</td>
                                <td className="text-end">
                                  <button type="button" className="btn btn-sm btn-link text-danger p-0"
                                          onClick={() => remove(row.id)}
                                          aria-label={`${t('harvestDelete')} ${row.harvest_date}`}>
                                    <i className="bi bi-trash" aria-hidden="true" />
                                  </button>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </>
        )}
      </div>
      <Footer />
    </>
  )
}
