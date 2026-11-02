// SMS advisory demonstration (Module 4).
import { useEffect, useRef, useState } from 'react'

import { api, errorMessage } from '../api/client'
import { ErrorBox, Footer, PageHeader } from '../components/Shared'
import { useApp } from '../context/AppContext'

const EXAMPLES = [
  'FERTILIZER',
  'Kodi ndingathire fetereza lero?',
  'When should I prune my tea?',
  'NYENGO',
  'my tea leaves have holes',
  'AREA Bvumbwe',
  'CALENDAR',
  'ALERTS',
  'ALERTS ON',
  'AREAS',
  'HELP',
  'LANG EN',
]

export default function SmsSimulator() {
  const { t } = useApp()
  const [phone, setPhone] = useState('0991234567')
  const [text, setText] = useState('')
  const [thread, setThread] = useState([])
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const [mode, setMode] = useState(null)
  const screenRef = useRef(null)

  useEffect(() => {
    api
      .get('/sms/status')
      .then(({ data }) => setMode(data))
      .catch(() => setMode(null))
  }, [])

  // Keep the newest message in view, the way a phone would.
  useEffect(() => {
    if (screenRef.current) {
      screenRef.current.scrollTop = screenRef.current.scrollHeight
    }
  }, [thread])

  const send = async (message) => {
    const body = (message ?? text).trim()
    if (!body || busy) return

    setBusy(true)
    setError(null)
    setThread((previous) => [...previous, { direction: 'in', message: body }])
    setText('')

    try {
      const { data } = await api.post('/sms/simulate', { from: phone, text: body })
      setThread((previous) => [
        ...previous,
        {
          direction: 'out',
          message: data.reply,
          topic: data.topic,
          characters: data.characters,
          language: data.language,
        },
      ])
    } catch (err) {
      setError(errorMessage(err, t('errorGeneric')) ?? 'network')
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <div className="container py-4">
        <PageHeader title={t('smsTitle')}>
          {mode && (
            <span className={`badge ${mode.mode === 'simulator' ? 'bg-secondary' : 'bg-success'}`}>
              {t('smsMode')}: {mode.mode}
            </span>
          )}
        </PageHeader>

        <div className="row g-4">
          <div className="col-lg-5">
            <p className="text-muted">{t('smsIntro')}</p>

            <div className="card card-mlimi mb-3">
              <div className="card-body">
                <label className="form-label" htmlFor="sms-phone">
                  {t('smsFrom')}
                </label>
                <input
                  id="sms-phone"
                  className="form-control mb-3"
                  value={phone}
                  onChange={(event) => setPhone(event.target.value)}
                />

                <label className="form-label" htmlFor="sms-text">
                  {t('smsMessage')}
                </label>
                <div className="input-group">
                  <input
                    id="sms-text"
                    className="form-control"
                    value={text}
                    placeholder="FERTILIZER"
                    maxLength={160}
                    onChange={(event) => setText(event.target.value)}
                    onKeyDown={(event) => {
                      if (event.key === 'Enter') send()
                    }}
                    disabled={busy}
                  />
                  <button className="btn btn-tea" onClick={() => send()} disabled={busy}>
                    {t('smsSend')}
                  </button>
                </div>
                <div className="form-text">
                  {text.length}/160 {t('smsChars')}
                </div>
              </div>
            </div>

            <div className="card card-mlimi">
              <div className="card-body">
                <div className="small text-muted mb-2">{t('smsTryThese')}</div>
                {EXAMPLES.map((example) => (
                  <span
                    className="chip"
                    key={example}
                    role="button"
                    tabIndex={0}
                    onClick={() => send(example)}
                    onKeyDown={(event) => {
                      if (event.key === 'Enter') send(example)
                    }}
                  >
                    {example}
                  </span>
                ))}
              </div>
            </div>
          </div>

          <div className="col-lg-7">
            <ErrorBox error={error} />
            <div className="phone-frame">
              <div className="text-center small fw-semibold text-muted mb-2 pb-2 border-bottom">
                MlimiSmart {'·'} {phone}
              </div>
              <div className="phone-screen" ref={screenRef}>
                {thread.length === 0 && (
                  <p className="text-center text-muted small mt-5">
                    {t('smsTryThese')}
                  </p>
                )}
                {thread.map((entry, index) => (
                  <div key={index}>
                    <div className={`sms-bubble ${entry.direction === 'in' ? 'sms-in' : 'sms-out'}`}>
                      {entry.message}
                    </div>
                    {entry.direction === 'out' && (
                      <div className="sms-meta mb-3">
                        {entry.topic} {'·'} {entry.characters} {t('smsChars')}{' '}
                        {'·'} {entry.language}
                      </div>
                    )}
                  </div>
                ))}
                {busy && (
                  <div className="sms-bubble sms-out text-muted">{t('asking')}</div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
      <Footer />
    </>
  )
}
