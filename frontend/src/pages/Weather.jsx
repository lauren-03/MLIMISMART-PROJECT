// Weather screen (Module 2), with an area selector so a farmer can also look
// at a neighbouring district.
import { useEffect, useState } from 'react'

import { api, errorMessage } from '../api/client'
import ForecastStrip from '../components/ForecastStrip'
import RainPredictionCard from '../components/RainPredictionCard'
import WeatherCard from '../components/WeatherCard'
import { AlertList, ErrorBox, Footer, PageHeader, Spinner } from '../components/Shared'
import { useApp } from '../context/AppContext'

export default function Weather() {
  const { farmer, language, t } = useApp()
  const [area, setArea] = useState(farmer.location)
  const [areas, setAreas] = useState([])
  const [weather, setWeather] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    api
      .get('/weather/locations')
      .then(({ data }) => setAreas(data))
      .catch(() => setAreas([]))
  }, [])

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    api
      .get('/weather', { params: { location: area, language } })
      .then(({ data }) => {
        if (!cancelled) setWeather(data)
      })
      .catch((err) => {
        if (!cancelled) setError(errorMessage(err, t('errorGeneric')) ?? 'network')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [area, language, t])

  return (
    <>
      <div className="container py-4">
        <PageHeader title={t('weatherTitle')} subtitle={weather?.district}>
          <div>
            <label className="form-label small text-muted mb-1" htmlFor="area">
              {t('changeArea')}
            </label>
            <select
              id="area"
              className="form-select"
              value={area}
              onChange={(event) => setArea(event.target.value)}
            >
              {['Thyolo', 'Mulanje'].map((district) => (
                <optgroup key={district} label={`${district} District`}>
                  {areas.filter((a) => a.district === district).map((a) => (
                    <option key={a.name} value={a.name}>
                      {a.kind === 'boma' ? `${a.name} Boma` : a.name}
                    </option>
                  ))}
                </optgroup>
              ))}
            </select>
          </div>
        </PageHeader>

        <ErrorBox error={error} />

        {loading ? (
          <Spinner />
        ) : (
          <>
            <div className="row g-4">
              <div className="col-lg-8">
                <WeatherCard weather={weather} />
              </div>
              <div className="col-lg-4">
                <RainPredictionCard location={area} />
                <h2 className="h6 text-uppercase text-muted mb-2">{t('alertsTitle')}</h2>
                <AlertList alerts={weather?.alerts} />
              </div>
            </div>
            <ForecastStrip forecast={weather?.forecast} />

            <div className="row g-4 mt-4">
              <div className="col-md-6">
                <img
                  src="/images/estate-hills.jpg"
                  alt="Tea fields under an overcast sky in the Malawi highlands"
                  className="section-photo"
                />
              </div>
              <div className="col-md-6">
                <div className="card card-mlimi h-100">
                  <div className="card-body">
                    <h2 className="h6 fw-semibold text-tea">{t('featureWeather')}</h2>
                    <p className="small text-muted mb-0">{t('featureWeatherText')}</p>
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
