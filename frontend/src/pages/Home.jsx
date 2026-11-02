// Public landing page.
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { api } from '../api/client'
import AreaSelect, { useAreas } from '../components/AreaSelect'
import ForecastStrip from '../components/ForecastStrip'
import { AlertList, Footer, Spinner } from '../components/Shared'
import WeatherCard from '../components/WeatherCard'
import { useApp } from '../context/AppContext'
import { TOPIC_LABELS } from '../i18n/translations'

const FEATURES = [
  { icon: 'cloud-sun', tone: '', title: 'featureWeather', text: 'featureWeatherText' },
  { icon: 'chat-square-text', tone: '', title: 'featureAdvice', text: 'featureAdviceText' },
  { icon: 'graph-up', tone: 'soil', title: 'featureModels', text: 'featureModelsText' },
  { icon: 'exclamation-triangle', tone: 'sun', title: 'featureAlerts', text: 'featureAlertsText' },
  { icon: 'calendar3', tone: '', title: 'featureCalendar', text: 'featureCalendarText' },
  { icon: 'basket', tone: 'soil', title: 'featureHarvest', text: 'featureHarvestText' },
  { icon: 'phone', tone: '', title: 'featureSms', text: 'featureSmsText' },
  { icon: 'translate', tone: 'sun', title: 'featureBilingual', text: 'featureBilingualText' },
]

const USSD_PREVIEW = `MLIMISMART
1. Weather
2. Farming Advice
3. Tea Advice
4. Ask a question
5. Language
6. My Area
7. This Month's Tasks
8. Weather Alerts
9. Exit`

export default function Home() {
  const { language, farmer, t } = useApp()
  const [weather, setWeather] = useState(null)
  const [area, setArea] = useState(farmer?.location ?? 'Thyolo')
  const areas = useAreas()

  useEffect(() => {
    let cancelled = false
    setWeather(null)
    api
      .get('/weather', { params: { location: area, language } })
      .then(({ data }) => !cancelled && setWeather(data))
      .catch(() => !cancelled && setWeather(false))
    return () => {
      cancelled = true
    }
  }, [area, language])

  return (
    <>
      {/* ------------------------------------------------------------ hero */}
      <section className="hero">
        <div className="container hero-content">
          <div className="row">
            <div className="col-lg-7">
              <span className="hero-badge mb-3">
                {t('heroBadge')}
              </span>
              <h1 className="mb-3">{t('heroTitle')}</h1>
              <p className="hero-lead mb-4">{t('heroText')}</p>
              <div className="d-flex gap-2 flex-wrap">
                {farmer ? (
                  <Link to="/dashboard" className="btn btn-leaf btn-lg">
                    {t('navDashboard')}
                  </Link>
                ) : (
                  <>
                    <Link to="/register" className="btn btn-leaf btn-lg">
                      {t('getStarted')}
                    </Link>
                    <Link to="/login" className="btn btn-outline-light btn-lg">
                      {t('haveAccount')}
                    </Link>
                  </>
                )}
              </div>
              <div className="hero-channels">
                <span>Website</span>
                <span>SMS</span>
                <span>USSD *384*211#</span>
                <span>English · Chichewa</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ------------------------------------------------- live weather */}
      <section className="container hero-overlap" aria-labelledby="live-weather">
        <div className="card card-mlimi p-3 p-md-4" style={{ boxShadow: 'var(--shadow-lg)' }}>
          <div className="d-flex justify-content-between align-items-end flex-wrap gap-3 mb-3">
            <div>
              <span className="eyebrow">{t('navWeather')}</span>
              <h2 id="live-weather" className="h4 text-tea mb-1">{t('liveWeatherTitle')}</h2>
              <p className="text-muted mb-0 small">{t('liveWeatherText')}</p>
            </div>
            <div style={{ minWidth: 230 }}>
              <label htmlFor="home-area" className="form-label small mb-1">{t('location')}</label>
              <AreaSelect id="home-area" value={area} onChange={setArea} />
            </div>
          </div>
          {weather === null && <Spinner />}
          {weather === false && <div className="alert alert-secondary">{t('cannotReachServer')}</div>}
          {weather && (
            <>
              <div className="row g-3">
                <div className="col-lg-8">
                  <WeatherCard weather={weather} />
                </div>
                <div className="col-lg-4">
                  <h3 className="h6 text-uppercase text-muted mb-2">{t('alertsTitle')}</h3>
                  <AlertList alerts={weather.alerts} />
                </div>
              </div>
              <ForecastStrip forecast={weather.forecast} />
            </>
          )}
        </div>
      </section>

      {/* ------------------------------------------------- how it works */}
      <section className="section" aria-labelledby="how">
        <div className="container">
          <div className="text-center mb-5">
            <span className="eyebrow">MlimiSmart</span>
            <h2 id="how" className="section-title">{t('howTitle')}</h2>
          </div>
          <div className="row g-4">
            {[
              { n: 1, icon: 'chat-square-text', title: 'how1', text: 'how1Text' },
              { n: 2, icon: 'cpu', title: 'how2', text: 'how2Text' },
              { n: 3, icon: 'check2-circle', title: 'how3', text: 'how3Text' },
            ].map((step) => (
              <div className="col-md-4" key={step.n}>
                <div className="step-card text-center">
                  <div className="step-number mx-auto">{step.n}</div>
                  <h3 className="h5 text-tea">{t(step.title)}</h3>
                  <p className="text-muted mb-0">{t(step.text)}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ----------------------------------------------------- features */}
      <section className="section section-white" aria-labelledby="features">
        <div className="container">
          <div className="row align-items-end mb-4 g-3">
            <div className="col-lg-7">
              <span className="eyebrow">{t('navTools')}</span>
              <h2 id="features" className="section-title">{t('featuresTitle')}</h2>
            </div>
          </div>
          <div className="row g-4">
            {FEATURES.map((feature) => (
              <div className="col-sm-6 col-lg-3" key={feature.title}>
                <div className="card card-mlimi card-hover h-100">
                  <div className="card-body">
                    <h3 className="h6 fw-bold">{t(feature.title)}</h3>
                    <p className="small text-muted mb-0">{t(feature.text)}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ------------------------------------------------------- topics */}
      <section className="section" aria-labelledby="topics">
        <div className="container">
          <div className="row g-5 align-items-center">
            <div className="col-lg-5">
              <img
                src="/images/two-leaves-bud.jpg"
                alt="A farmer's hand holding two leaves and a bud, the correct plucking standard"
                className="section-photo"
                style={{ minHeight: 360 }}
              />
            </div>
            <div className="col-lg-7">
              <span className="eyebrow">{t('navAsk')}</span>
              <h2 id="topics" className="section-title">{t('topicsTitle')}</h2>
              <div className="mb-4">
                {Object.entries(TOPIC_LABELS)
                  .filter(([key]) => key !== 'general')
                  .map(([key, labels]) => (
                    <span className="chip" key={key} style={{ cursor: 'default' }}>
                      {labels[language]}
                    </span>
                  ))}
              </div>
              <div className="row g-3">
                <div className="col-sm-6">
                  <Link to={farmer ? '/harvest' : '/register'} className="card card-mlimi card-hover overflow-hidden">
                    <img src="/images/farmer-plucking.jpg" alt="" className="card-photo w-100" />
                    <div className="card-body">
                      <h3 className="h6 fw-bold mb-1">
                        {t('featureHarvest')}
                      </h3>
                      <p className="small text-muted mb-0">{t('featureHarvestText')}</p>
                    </div>
                  </Link>
                </div>
                <div className="col-sm-6">
                  <Link to="/calendar" className="card card-mlimi card-hover overflow-hidden">
                    <img src="/images/plucking-rows.jpg" alt="" className="card-photo w-100" />
                    <div className="card-body">
                      <h3 className="h6 fw-bold mb-1">
                        {t('featureCalendar')}
                      </h3>
                      <p className="small text-muted mb-0">{t('featureCalendarText')}</p>
                    </div>
                  </Link>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* -------------------------------------------------------- areas */}
      <section className="section section-white" aria-labelledby="areas">
        <div className="container">
          <div className="row g-5 align-items-center">
            <div className="col-lg-7">
              <span className="eyebrow">Thyolo · Mulanje</span>
              <h2 id="areas" className="section-title">{t('areasTitle')}</h2>
              <p className="section-lead mb-4">{t('areasText')}</p>
              {['Thyolo', 'Mulanje'].map((district) => (
                <div key={district} className="mb-3">
                  <h3 className="h6 fw-bold text-tea">{district} District</h3>
                  {areas
                    .filter((a) => a.district === district)
                    .map((a) => (
                      <span className="area-chip" key={a.name}>
                        {a.kind === 'boma' ? `${a.name} Boma` : a.name}
                      </span>
                    ))}
                </div>
              ))}
              <Link to="/map" className="btn btn-outline-tea mt-2">
                {t('seeMap')}
              </Link>
            </div>
            <div className="col-lg-5">
              <img
                src="/images/estate-hills.jpg"
                alt="Tea estates on the hills of the Shire Highlands"
                className="section-photo"
                style={{ minHeight: 380 }}
              />
            </div>
          </div>
        </div>
      </section>

      {/* ----------------------------------------------- basic phones */}
      <section className="section section-green" aria-labelledby="phones">
        <div className="container">
          <div className="row g-5 align-items-center">
            <div className="col-lg-6">
              <span className="eyebrow">USSD · SMS</span>
              <h2 id="phones" className="section-title">{t('phonesTitle')}</h2>
              <p className="section-lead mb-4">{t('phonesText')}</p>
              <div className="d-flex gap-2 flex-wrap">
                <Link to="/ussd" className="btn btn-leaf btn-lg">
                  {t('tryUssd')}
                </Link>
                <Link to="/sms" className="btn btn-outline-light btn-lg">
                  {t('trySms')}
                </Link>
              </div>
              <img
                src="/images/farmers-smiling.jpg"
                alt="Smallholder tea farmers in the field"
                className="section-photo mt-4 d-none d-lg-block"
                style={{ minHeight: 200, maxHeight: 240 }}
              />
            </div>
            <div className="col-lg-6">
              <div className="ussd-phone">
                <div className="ussd-screen">
                  <pre className="ussd-text">{USSD_PREVIEW}</pre>
                  <div className="ussd-status">*384*211# · Airtel / TNM</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <Footer flush />
    </>
  )
}
