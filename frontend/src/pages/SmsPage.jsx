// SMS advice (Module 4): the number farmers text, what they can send, and for
// the administrator the real messages coming in and going out.
import { useEffect, useState } from 'react'

import { api } from '../api/client'
import { Footer, PageHeader } from '../components/Shared'
import { useApp } from '../context/AppContext'

const WORDS = [
  ['FERTILIZER', 'Fertilizer advice for today'],
  ['NYENGO / WEATHER', "Today's weather for your area"],
  ['AREA Bvumbwe', 'Set your area'],
  ['CALENDAR', "This month's tea work"],
  ['ALERTS ON', 'Weather warnings by SMS'],
  ['LANG EN / LANG NY', 'Change language'],
  ['HELP', 'Everything you can send'],
]

const when = (v) => (v ? new Date(v).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' }) : '')

export default function SmsPage() {
  const { isAdmin, t } = useApp()
  const [status, setStatus] = useState(null)
  const [log, setLog] = useState([])

  useEffect(() => {
    api.get('/sms/status').then(({ data }) => setStatus(data)).catch(() => setStatus(null))
  }, [])

  useEffect(() => {
    if (!isAdmin) return undefined
    const load = () => api.get('/admin/sms-logs', { params: { limit: 30 } })
      .then(({ data }) => setLog(data.filter((row) => row.gateway !== 'simulator')))
      .catch(() => {})
    load()
    const timer = setInterval(load, 5000)
    return () => clearInterval(timer)
  }, [isAdmin])

  const live = status?.mode && status.mode !== 'simulator'

  return (
    <>
      <div className="container py-4">
        <PageHeader title={t('smsTitle')} subtitle={t('smsLead')} />

        <div className="row g-4">
          <div className="col-lg-5">
            <div className="card card-mlimi mb-3">
              <div className="card-body">
                {live ? (
                  <>
                    <div className="small text-muted">{t('smsTextTo')}</div>
                    <div className="sms-number">{status.number || '—'}</div>
                    <p className="small mb-0">
                      <span className="badge bg-success me-1">{t('live')}</span>
                      {t('smsVia')} {status.gateway}
                    </p>
                  </>
                ) : (
                  <p className="mb-0">{t('smsNotConnected')}</p>
                )}
              </div>
            </div>

            <div className="card card-mlimi">
              <div className="card-body">
                <h2 className="h6 fw-semibold text-tea">{t('smsWords')}</h2>
                <table className="table table-sm small mb-2">
                  <tbody>
                    {WORDS.map(([word, meaning]) => (
                      <tr key={word}><td className="fw-semibold">{word}</td><td>{meaning}</td></tr>
                    ))}
                  </tbody>
                </table>
                <p className="small text-muted mb-0">{t('smsFreeText')}</p>
              </div>
            </div>
          </div>

          {isAdmin && (
            <div className="col-lg-7">
              <div className="card card-mlimi">
                <div className="card-body">
                  <h2 className="h6 fw-semibold text-tea">{t('smsLiveLog')}</h2>
                  {log.length === 0 ? (
                    <p className="small text-muted mb-0">{t('smsNoMessages')}</p>
                  ) : (
                    <div className="sms-log">
                      {log.map((row) => (
                        <div key={row.id} className={`sms-bubble ${row.direction === 'IN' ? 'sms-in' : 'sms-out'}`}>
                          <div>{row.message}</div>
                          <div className="sms-meta">
                            {row.direction === 'IN' ? row.phone : `→ ${row.phone}`} · {when(row.created_at)}
                            {row.status !== 'ok' && ` · ${row.status}`}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
      <Footer />
    </>
  )
}
