// Advisory history. Shows the channel each question came through, so a farmer
// who asked by SMS sees those answers here as well.
import { useEffect, useState } from 'react'

import { api, errorMessage } from '../api/client'
import { ErrorBox, Footer, PageHeader, Spinner } from '../components/Shared'
import { useApp } from '../context/AppContext'
import { topicLabel } from '../i18n/translations'

const URGENCY_BADGE = {
  urgent: 'bg-danger',
  caution: 'bg-warning text-dark',
  normal: 'bg-success',
}

export default function History() {
  const { language, t } = useApp()
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    api
      .get('/advice/history')
      .then(({ data }) => setItems(data))
      .catch((err) => setError(errorMessage(err, t('errorGeneric')) ?? 'network'))
      .finally(() => setLoading(false))
  }, [t])

  return (
    <>
      <div className="container py-4">
        <PageHeader title={t('historyTitle')} />
        <ErrorBox error={error} />

        {loading ? (
          <Spinner />
        ) : items.length === 0 ? (
          <div className="alert alert-secondary">{t('noHistory')}</div>
        ) : (
          items.map((item) => (
            <div className="card card-mlimi mb-3" key={item.request_id}>
              <div className="card-body">
                <div className="d-flex justify-content-between flex-wrap gap-2 mb-2">
                  <div>
                    <span className="badge bg-light text-tea border me-2">
                      {topicLabel(item.topic, language)}
                    </span>
                    <span className={`badge ${URGENCY_BADGE[item.urgency] ?? 'bg-secondary'}`}>
                      {t(item.urgency ?? 'normal')}
                    </span>
                    <span className="badge bg-secondary ms-2">{item.channel}</span>
                  </div>
                  <span className="small text-muted">
                    {item.created_at ? new Date(item.created_at).toLocaleString() : ''}
                  </span>
                </div>
                <p className="fw-semibold mb-1">
                  {'“'}
                  {item.question}
                  {'”'}
                </p>
                <p className="mb-0 text-muted">{item.advice}</p>
              </div>
            </div>
          ))
        )}
      </div>
      <Footer />
    </>
  )
}
