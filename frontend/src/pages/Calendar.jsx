// Tea farming calendar: twelve months of routine work for Thyolo and Mulanje,
// with the current month highlighted and shown first on small screens.
import { useEffect, useState } from 'react'

import { api, errorMessage } from '../api/client'
import { ErrorBox, Footer, PageHead, Spinner } from '../components/Shared'
import { useApp } from '../context/AppContext'
import { seasonLabel } from '../i18n/translations'

export default function Calendar() {
  const { language, t } = useApp()
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    let cancelled = false
    api
      .get('/calendar', { params: { language } })
      .then(({ data: body }) => !cancelled && setData(body))
      .catch((err) => !cancelled && setError(errorMessage(err, t('errorGeneric')) ?? 'network'))
    return () => {
      cancelled = true
    }
  }, [language, t])

  // Current month first, then the rest of the year in order from there.
  const ordered = data
    ? [...data.months.slice(data.current_month - 1), ...data.months.slice(0, data.current_month - 1)]
    : []

  return (
    <>
      <PageHead icon="calendar3" title={t('calendarTitle')} intro={t('calendarIntro')} />
      <div className="container">
        <ErrorBox error={error} />
        {!data && !error && <Spinner />}
        <div className="row g-3">
          {ordered.map((month) => {
            const current = month.month === data.current_month
            return (
              <div className={current ? 'col-12 col-lg-8' : 'col-md-6 col-lg-4'} key={month.month}>
                <article className={`month-card${current ? ' current' : ''}`}>
                  <div className="d-flex justify-content-between align-items-start mb-2 gap-2">
                    <div>
                      <h2 className={current ? 'h4 mb-0 text-tea' : 'h5 mb-0 text-tea'}>{month.name}</h2>
                      <div className={`small fw-semibold season-${month.season}`}>
                        {seasonLabel(month.season, language)}
                      </div>
                    </div>
                    {current && <span className="badge bg-success">{t('nowBadge')}</span>}
                  </div>
                  <p className="fw-semibold mb-3">{month.focus}</p>
                  {month.tasks.map((task) => (
                    <div className="task" key={task.text}>
                      <span>{task.text}</span>
                    </div>
                  ))}
                </article>
              </div>
            )
          })}
        </div>
      </div>
      <Footer />
    </>
  )
}
