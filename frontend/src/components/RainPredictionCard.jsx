// Tomorrow's chance of rain from MlimiSmart's own trained rain model,
// with the model's tested accuracy.
import { useEffect, useState } from 'react'

import { api } from '../api/client'
import { useApp } from '../context/AppContext'

const pct = (value) => (value === null || value === undefined ? '--' : `${Math.round(value * 100)}%`)

export default function RainPredictionCard({ location }) {
  const { language, t } = useApp()
  const [data, setData] = useState(null)

  useEffect(() => {
    let cancelled = false
    api
      .get('/weather/prediction', { params: { location } })
      .then(({ data: result }) => !cancelled && setData(result))
      .catch(() => !cancelled && setData(null))
    return () => {
      cancelled = true
    }
  }, [location])

  const prediction = data?.prediction
  if (!prediction) return null

  const day = new Date(prediction.target_day).toLocaleDateString(
    language === 'NY' ? 'ny-MW' : 'en-GB', { weekday: 'long', day: 'numeric', month: 'short' })
  const metrics = data.model?.metrics

  return (
    <div className="card card-mlimi mb-3">
      <div className="card-body">
        <h2 className="h6 fw-semibold text-tea mb-1">{t('rainModelTitle')}</h2>
        <div className="d-flex align-items-baseline gap-2">
          <span className="display-6 fw-semibold">{pct(prediction.probability)}</span>
          <span className="text-muted">{t('rainChanceOn')} {day}</span>
        </div>
        <p className="mb-2">{prediction.will_rain ? t('rainExpected') : t('rainNotExpected')}</p>
        {metrics && (
          <p className="small text-muted mb-0">
            {t('rainModelVersion')} {prediction.model_version} · {t('testedAccuracy')} {pct(metrics.accuracy)}
            {data.live?.checked > 0 && ` · ${t('liveAccuracy')} ${pct(data.live.accuracy)} (${data.live.checked})`}
          </p>
        )}
      </div>
    </div>
  )
}
