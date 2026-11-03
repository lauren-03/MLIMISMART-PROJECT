// Farmer dashboard.
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { api, errorMessage } from '../api/client'
import AdviceCard from '../components/AdviceCard'
import ForecastStrip from '../components/ForecastStrip'
import { AlertList, ErrorBox, Footer, Spinner } from '../components/Shared'
import RainPredictionCard from '../components/RainPredictionCard'
import WeatherCard from '../components/WeatherCard'
import { useApp } from '../context/AppContext'
import { seasonLabel } from '../i18n/translations'

function greetingKey() {
  const hour = new Date().getHours()
  if (hour < 12) return 'goodMorning'
  if (hour < 17) return 'goodAfternoon'
  return 'goodEvening'
}

const QUICK = [
  { to: '/ask', icon: 'chat-square-text', label: 'navAsk' },
  { to: '/harvest', icon: 'basket', label: 'navHarvest' },
  { to: '/calendar', icon: 'calendar3', label: 'navCalendar' },
  { to: '/weather', icon: 'cloud-sun', label: 'navWeather' },
  { to: '/map', icon: 'geo-alt', label: 'navMap' },
]

export default function Dashboard() {
  const { farmer, language, t } = useApp()
  const [weather, setWeather] = useState(null)
  const [daily, setDaily] = useState(null)
  const [month, setMonth] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    Promise.all([
      api.get('/weather/mine', { params: { language } }),
      api.get('/advice/daily'),
      api.get('/calendar', { params: { language } }),
    ])
      .then(([weatherResponse, dailyResponse, calendarResponse]) => {
        if (cancelled) return
        setWeather(weatherResponse.data)
        setDaily(dailyResponse.data)
        const cal = calendarResponse.data
        setMonth(cal.months[cal.current_month - 1])
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
  }, [language, t])

  if (loading) return <Spinner />

  return (
    <>
      <header className="page-head">
        <div className="container d-flex justify-content-between align-items-end flex-wrap gap-3">
          <div>
            <h1 className="h2">
              {t(greetingKey())}, {farmer.name.split(' ')[0]}
            </h1>
            <p>
              {farmer.location}
              {weather?.district && weather.district !== farmer.location ? `, ${weather.district}` : ''}
              {daily?.season ? ` · ${seasonLabel(daily.season, language)}` : ''}
            </p>
          </div>
          <Link to="/weather" className="btn btn-leaf">
            {t('viewForecast')}
          </Link>
        </div>
      </header>

      <div className="container">
        <ErrorBox error={error} />

        <div className="row g-4">
          <div className="col-lg-5">
            <WeatherCard weather={weather} />
            <RainPredictionCard location={farmer.location} />
          </div>
          <div className="col-lg-7">
            <h2 className="h6 text-uppercase text-muted mb-2">{t('todaysAdvice')}</h2>
            <AdviceCard advice={daily} showReasoning={false} />
            <h2 className="h6 text-uppercase text-muted mb-2 mt-3">{t('alertsTitle')}</h2>
            <AlertList alerts={weather?.alerts} />
          </div>
        </div>

        <ForecastStrip forecast={weather?.forecast} />

        <div className="row g-4 mt-1">
          <div className="col-lg-5">
            <h2 className="h6 text-uppercase text-muted mb-2">{t('quickActions')}</h2>
            <div className="row g-2">
              {QUICK.map((item) => (
                <div className="col-4" key={item.to}>
                  <Link to={item.to} className="quick-action">
                    {t(item.label)}
                  </Link>
                </div>
              ))}
            </div>
          </div>
          <div className="col-lg-7">
            {month && (
              <div className="month-card current h-100">
                <div className="d-flex justify-content-between align-items-start mb-2">
                  <h2 className="h5 text-tea mb-0">
                    {t('thisMonth')}: {month.name}
                  </h2>
                  <Link to="/calendar" className="small fw-semibold">{t('fullCalendar')}</Link>
                </div>
                <p className="fw-semibold mb-2">{month.focus}</p>
                {month.tasks.map((task) => (
                  <div className="task" key={task.text}>
                    <span>{task.text}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

      </div>
      <Footer />
    </>
  )
}
