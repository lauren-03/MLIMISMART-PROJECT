// Ask-for-advice page (Module 3). New answers appear at the top of the list.
import { useState } from 'react'

import { api, errorMessage } from '../api/client'
import AdviceCard from '../components/AdviceCard'
import QuestionBox from '../components/QuestionBox'
import { ErrorBox, Footer, PageHeader, Spinner } from '../components/Shared'
import { useApp } from '../context/AppContext'

export default function Ask() {
  const { farmer, t } = useApp()
  const [answers, setAnswers] = useState([])
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)

  const ask = async (question) => {
    setBusy(true)
    setError(null)
    try {
      const { data } = await api.post('/advice/ask', { question })
      setAnswers((previous) => [{ ...data, question }, ...previous])
    } catch (err) {
      setError(errorMessage(err, t('errorGeneric')) ?? 'network')
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <div className="container py-4">
        <PageHeader title={t('askTitle')} subtitle={`${t('askLead')} · ${farmer.location}`} />

        <div className="row g-4">
          <div className="col-lg-8">
            <ErrorBox error={error} />
            <QuestionBox onAsk={ask} busy={busy} />
            {busy && <Spinner label={t('asking')} />}

            {answers.map((answer, index) => (
              <div key={`${answer.request_id}-${index}`}>
                <p className="fw-semibold text-tea mb-2">
                  {'“'}
                  {answer.question}
                  {'”'}
                </p>
                <AdviceCard advice={answer} />
              </div>
            ))}
          </div>

          <aside className="col-lg-4">
            <div className="card card-mlimi mb-3">
              <div className="card-body">
                <h2 className="h6 fw-semibold text-tea">{t('askHelpsTitle')}</h2>
                <p className="small mb-2">{t('askHelpsText')}</p>
                <p className="small text-muted mb-0">{t('askCanAdvise')}</p>
              </div>
            </div>
            <img
              src="/images/farmer-plucking.jpg"
              alt="A smallholder farmer plucking tea"
              className="ask-photo d-none d-lg-block"
            />
          </aside>
        </div>
      </div>
      <Footer />
    </>
  )
}
