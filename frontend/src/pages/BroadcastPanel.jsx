// Admin: send weather alerts to subscribed farmers.
import { useEffect, useState } from 'react'

import { api, errorMessage } from '../api/client'
import AreaSelect from '../components/AreaSelect'
import { ErrorBox } from '../components/Shared'
import { useApp } from '../context/AppContext'

export default function BroadcastPanel() {
  const { t } = useApp()
  const [scope, setScope] = useState('district')
  const [district, setDistrict] = useState('Thyolo')
  const [area, setArea] = useState('Thyolo')
  const [form, setForm] = useState({ title: '', message_en: '', message_ny: '' })
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const [sent, setSent] = useState(null)
  const [history, setHistory] = useState([])

  const loadHistory = () =>
    api.get('/admin/broadcasts').then(({ data }) => setHistory(data)).catch(() => {})

  useEffect(() => {
    loadHistory()
  }, [])

  const draft = async () => {
    setBusy(true)
    setError(null)
    try {
      const source = scope === 'area' ? area : district
      const { data } = await api.get('/admin/broadcast/suggest', { params: { location: source } })
      setForm({ title: data.title, message_en: data.message_en, message_ny: data.message_ny })
    } catch (err) {
      setError(errorMessage(err, t('errorGeneric')) ?? 'network')
    } finally {
      setBusy(false)
    }
  }

  const send = async (event) => {
    event.preventDefault()
    setBusy(true)
    setError(null)
    setSent(null)
    try {
      const target =
        scope === 'all' ? {} : scope === 'district' ? { district } : { location: area }
      const { data } = await api.post('/admin/broadcast', { ...form, ...target })
      setSent(data)
      loadHistory()
    } catch (err) {
      setError(errorMessage(err, t('errorGeneric')) ?? 'network')
    } finally {
      setBusy(false)
    }
  }

  const set = (key) => (event) => setForm((f) => ({ ...f, [key]: event.target.value }))

  return (
    <div className="row g-4">
      <div className="col-lg-7">
        <form className="card card-mlimi" onSubmit={send}>
          <div className="card-body">
            <h2 className="h5 text-tea">
              {t('broadcastTitle')}
            </h2>
            <p className="small text-muted">{t('broadcastIntro')}</p>
            <ErrorBox error={error} />
            {sent && (
              <div className="alert alert-success" role="status">
                {t('broadcastSent')}: {sent.target} — {sent.sent}/{sent.recipients} SMS ({sent.gateway})
              </div>
            )}

            <fieldset className="mb-3">
              <legend className="form-label fs-6">{t('broadcastTarget')}</legend>
              <div className="d-flex flex-wrap gap-3 align-items-center">
                {[
                  { id: 'all', label: t('allDistricts') },
                  { id: 'district', label: t('district') },
                  { id: 'area', label: t('location') },
                ].map((option) => (
                  <div className="form-check" key={option.id}>
                    <input className="form-check-input" type="radio" name="scope" id={`scope-${option.id}`}
                           checked={scope === option.id} onChange={() => setScope(option.id)} />
                    <label className="form-check-label" htmlFor={`scope-${option.id}`}>{option.label}</label>
                  </div>
                ))}
              </div>
              <div className="row g-2 mt-1">
                {scope === 'district' && (
                  <div className="col-sm-6">
                    <select className="form-select" value={district} aria-label={t('district')}
                            onChange={(e) => setDistrict(e.target.value)}>
                      <option>Thyolo</option>
                      <option>Mulanje</option>
                    </select>
                  </div>
                )}
                {scope === 'area' && (
                  <div className="col-sm-6">
                    <AreaSelect id="broadcast-area" value={area} onChange={setArea}
                                aria-label={t('location')} />
                  </div>
                )}
                <div className="col-sm-6">
                  <button type="button" className="btn btn-outline-tea w-100" onClick={draft} disabled={busy}>
                    {t('broadcastDraft')}
                  </button>
                </div>
              </div>
            </fieldset>

            <div className="mb-3">
              <label htmlFor="b-title" className="form-label">{t('title')}</label>
              <input id="b-title" className="form-control" required minLength={2} maxLength={120}
                     value={form.title} onChange={set('title')} />
            </div>
            <div className="mb-3">
              <label htmlFor="b-en" className="form-label">{t('messageEn')}</label>
              <textarea id="b-en" className="form-control" rows={3} required minLength={5} maxLength={459}
                        value={form.message_en} onChange={set('message_en')} />
              <div className="form-text">{form.message_en.length} / 459</div>
            </div>
            <div className="mb-3">
              <label htmlFor="b-ny" className="form-label">{t('messageNy')}</label>
              <textarea id="b-ny" className="form-control" rows={3} required minLength={5} maxLength={459}
                        value={form.message_ny} onChange={set('message_ny')} />
              <div className="form-text">{form.message_ny.length} / 459</div>
            </div>
            <button className="btn btn-tea btn-lg" disabled={busy}>
              {t('broadcastSend')}
            </button>
          </div>
        </form>
      </div>

      <div className="col-lg-5">
        <div className="card card-mlimi">
          <div className="card-body">
            <h2 className="h6 text-uppercase text-muted">{t('broadcastHistory')}</h2>
            {history.length === 0 && <p className="small text-muted mb-0">—</p>}
            <ul className="list-unstyled mb-0">
              {history.map((item) => (
                <li key={item.id} className="border-bottom py-2 small">
                  <div className="d-flex justify-content-between gap-2">
                    <strong>{item.title}</strong>
                    <span className="badge bg-light text-tea border">{item.recipients} SMS</span>
                  </div>
                  <div className="text-muted">
                    {item.target} · {String(item.created_at).replace('T', ' ').slice(0, 16)}
                  </div>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}
