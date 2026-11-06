// USSD advice (Module 7): the code to dial, how to reach it, and for the
// administrator the gateway address and the real sessions.
import { useEffect, useState } from 'react'

import { api } from '../api/client'
import { Footer, PageHeader } from '../components/Shared'
import { useApp } from '../context/AppContext'

const SANDBOX_PHONE = 'https://developers.africastalking.com/simulator'
const when = (v) => (v ? new Date(v).toLocaleString('en-GB', { hour: '2-digit', minute: '2-digit', day: 'numeric', month: 'short' }) : '')

export default function UssdPage() {
  const { isAdmin, t } = useApp()
  const [status, setStatus] = useState(null)
  const [sessions, setSessions] = useState([])

  useEffect(() => {
    api.get('/ussd/status').then(({ data }) => setStatus(data)).catch(() => setStatus(null))
  }, [])

  useEffect(() => {
    if (!isAdmin) return undefined
    const load = () => api.get('/admin/ussd-sessions', { params: { limit: 20 } })
      .then(({ data }) => setSessions(data.filter((row) => row.gateway === 'africastalking')))
      .catch(() => {})
    load()
    const timer = setInterval(load, 5000)
    return () => clearInterval(timer)
  }, [isAdmin])

  const sandbox = status?.mode === 'africastalking-sandbox'
  const live = status?.mode && status.mode !== 'simulator'

  return (
    <>
      <div className="container py-4">
        <PageHeader title={t('ussdTitle')} subtitle={t('ussdLead')} />

        <div className="row g-4">
          <div className="col-lg-5">
            <div className="card card-mlimi mb-3">
              <div className="card-body">
                <div className="small text-muted">{t('ussdDial')}</div>
                <div className="sms-number">{status?.service_code || '*384*36247#'}</div>
                {live ? (
                  <p className="small mb-0">
                    <span className="badge bg-success me-1">{t('live')}</span>
                    {t('ussdVia')}
                  </p>
                ) : (
                  <p className="small mb-0">{t('ussdNotConnected')}</p>
                )}
              </div>
            </div>

            {sandbox && (
              <div className="card card-mlimi">
                <div className="card-body">
                  <h2 className="h6 fw-semibold text-tea">{t('ussdHowTitle')}</h2>
                  <ol className="small mb-2 ps-3">
                    <li>{t('ussdStep1')} <a href={SANDBOX_PHONE} target="_blank" rel="noreferrer">{t('ussdSandboxPhone')}</a>.</li>
                    <li>{t('ussdStep2')}</li>
                    <li>{t('ussdStep3')} <strong>{status.service_code}</strong>.</li>
                  </ol>
                  <p className="small text-muted mb-0">{t('ussdSandboxNote')}</p>
                </div>
              </div>
            )}
          </div>

          {isAdmin && (
            <div className="col-lg-7">
              <div className="card card-mlimi mb-3">
                <div className="card-body">
                  <h2 className="h6 fw-semibold text-tea">{t('ussdCallback')}</h2>
                  {status?.callback_url ? (
                    <code className="d-block user-select-all">{status.callback_url}</code>
                  ) : (
                    <p className="small text-muted mb-0">{t('ussdNoCallback')}</p>
                  )}
                </div>
              </div>
              <div className="card card-mlimi">
                <div className="card-body">
                  <h2 className="h6 fw-semibold text-tea">{t('ussdLiveLog')}</h2>
                  {sessions.length === 0 ? (
                    <p className="small text-muted mb-0">{t('ussdNoSessions')}</p>
                  ) : (
                    <table className="table table-sm small mb-0">
                      <thead><tr><th>{t('phone')}</th><th>{t('ussdLastInput')}</th><th>{t('ussdScreens')}</th><th></th></tr></thead>
                      <tbody>
                        {sessions.map((row) => (
                          <tr key={row.id}>
                            <td>{row.phone}</td>
                            <td>{row.last_input || '—'}</td>
                            <td>{row.screens_served}</td>
                            <td className="text-muted">{when(row.created_at)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
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
