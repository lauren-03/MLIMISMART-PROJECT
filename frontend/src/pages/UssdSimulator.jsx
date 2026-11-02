// USSD advisory demonstration (Module 7).
import { useEffect, useRef, useState } from 'react'

import { api, errorMessage } from '../api/client'
import { ErrorBox, Footer, PageHeader } from '../components/Shared'
import { useApp } from '../context/AppContext'

export default function UssdSimulator() {
  const { t } = useApp()
  const [phone, setPhone] = useState('0991234567')
  const [status, setStatus] = useState(null)
  const [session, setSession] = useState(null)
  const [screen, setScreen] = useState(null)
  const [reply, setReply] = useState('')
  const [history, setHistory] = useState([])
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const replyRef = useRef(null)

  useEffect(() => {
    api
      .get('/ussd/status')
      .then(({ data }) => setStatus(data))
      .catch(() => setStatus(null))
  }, [])

  // Keep focus in the reply box so the demonstration flows without reaching
  // for the mouse between screens.
  useEffect(() => {
    if (screen && !screen.is_end && replyRef.current) replyRef.current.focus()
  }, [screen])

  const send = async (accumulated, sessionId) => {
    setBusy(true)
    setError(null)
    try {
      const { data } = await api.post('/ussd/simulate', {
        phone,
        text: accumulated,
        sessionId: sessionId ?? null,
      })
      setScreen(data)
      setSession({ sessionId: data.session_id, text: accumulated })
      setHistory((previous) => [
        ...previous,
        { input: accumulated, isEnd: data.is_end },
      ])
    } catch (err) {
      setError(errorMessage(err, t('errorGeneric')) ?? 'network')
    } finally {
      setBusy(false)
    }
  }

  const dial = () => {
    setHistory([])
    setReply('')
    send('', null)
  }

  const hangUp = () => {
    setSession(null)
    setScreen(null)
    setHistory([])
    setReply('')
  }

  // The gateway resends the whole accumulated input, joined by asterisks.
  const press = (entry) => {
    if (!session || busy) return
    const accumulated = session.text ? `${session.text}*${entry}` : entry
    send(accumulated, session.sessionId)
  }

  const submitReply = (event) => {
    event.preventDefault()
    const entry = reply.trim()
    if (!entry) return
    setReply('')
    press(entry)
  }

  const active = screen && !screen.is_end

  return (
    <>
      <div className="container py-4">
        <PageHeader title={t('ussdTitle')}>
          {status && (
            <div className="text-end">
              <span
                className={`badge ${status.mode === 'simulator' ? 'bg-secondary' : 'bg-success'}`}
              >
                {t('smsMode')}: {status.mode}
              </span>
              <div className="small text-muted mt-1">
                {t('ussdServiceCode')}: <code>{status.service_code}</code>
              </div>
            </div>
          )}
        </PageHeader>

        <div className="row g-4">
          <div className="col-lg-5">
            <p className="text-muted">{t('ussdIntro')}</p>

            <div className="card card-mlimi mb-3">
              <div className="card-body">
                <label className="form-label" htmlFor="ussd-phone">
                  {t('smsFrom')}
                </label>
                <input
                  id="ussd-phone"
                  className="form-control mb-3"
                  value={phone}
                  onChange={(event) => setPhone(event.target.value)}
                  disabled={Boolean(active)}
                />

                {active ? (
                  <button className="btn btn-outline-danger w-100" onClick={hangUp}>
                    {t('ussdHangUp')}
                  </button>
                ) : (
                  <button className="btn btn-tea w-100" onClick={dial} disabled={busy}>
                    {screen ? t('ussdRestart') : t('ussdDial')}{' '}
                    {status?.service_code ?? ''}
                  </button>
                )}
              </div>
            </div>

            {history.length > 0 && (
              <div className="card card-mlimi">
                <div className="card-body">
                  <div className="small text-muted mb-2">{t('ussdInputTrail')}</div>
                  {history.map((entry, index) => (
                    <div key={index} className="small mb-1">
                      <code className="text-tea">
                        {entry.input === ''
                          ? status?.service_code ?? '*384*211#'
                          : entry.input}
                      </code>
                      {entry.isEnd && <span className="badge bg-secondary ms-2">END</span>}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="col-lg-7">
            <ErrorBox error={error} />

            <div className="ussd-phone">
              <div className="ussd-screen">
                {!screen ? (
                  <div className="ussd-idle">{t('ussdNotDialled')}</div>
                ) : (
                  <>
                    <pre className="ussd-text">{screen.message}</pre>
                    <div className="ussd-status">
                      {screen.characters} {t('ussdScreenChars')}
                      {' · '}
                      {screen.language}
                      {screen.is_end ? ` · ${t('ussdSessionEnd')}` : ''}
                    </div>
                  </>
                )}
              </div>

              <form className="ussd-keypad" onSubmit={submitReply}>
                <input
                  ref={replyRef}
                  className="form-control"
                  placeholder={t('ussdReply')}
                  value={reply}
                  onChange={(event) => setReply(event.target.value)}
                  disabled={!active || busy}
                  maxLength={160}
                />
                <button
                  className="btn btn-tea"
                  type="submit"
                  disabled={!active || busy || !reply.trim()}
                >
                  {t('ussdSend')}
                </button>
              </form>

              {active && (
                <div className="ussd-quickkeys">
                  {['1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '98'].map((key) => (
                    <button
                      key={key}
                      className="btn btn-sm btn-outline-light"
                      onClick={() => press(key)}
                      disabled={busy}
                    >
                      {key}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
      <Footer />
    </>
  )
}
