// Small presentational pieces used across several screens.
import { Link, Navigate } from 'react-router-dom'

import { useApp } from '../context/AppContext'

export function Spinner({ label }) {
  const { t } = useApp()
  return (
    <div className="text-center py-5" role="status" aria-live="polite">
      <div className="spinner-border text-success" aria-hidden="true" />
      <div className="mt-2 text-muted">{label ?? t('loading')}</div>
    </div>
  )
}

// A network failure and a rejected request need different messages: one means
// the backend is not running, the other is a real API error.
export function ErrorBox({ error }) {
  const { t } = useApp()
  if (!error) return null
  return (
    <div className="alert alert-danger d-flex gap-2 align-items-start" role="alert">
      <span>{error === 'network' ? t('cannotReachServer') : error}</span>
    </div>
  )
}

export function PageHeader({ title, subtitle, children }) {
  return (
    <div className="d-flex justify-content-between align-items-end flex-wrap gap-3 mb-4">
      <div>
        <h1 className="h3 text-tea mb-1">{title}</h1>
        {subtitle && <p className="text-muted mb-0">{subtitle}</p>}
      </div>
      {children}
    </div>
  )
}

// The green banner at the top of the farmer tool pages. One clear title and
// one sentence on what the page is for, so nobody has to guess.
export function PageHead({ icon, title, intro, children }) {
  return (
    <header className="page-head">
      <div className="container d-flex justify-content-between align-items-end flex-wrap gap-3">
        <div className="d-flex gap-3 align-items-start">
          <div>
            <h1 className="h2">{title}</h1>
            {intro && <p>{intro}</p>}
          </div>
        </div>
        {children}
      </div>
    </header>
  )
}

export function StatTile({ figure, caption, icon = 'bar-chart' }) {
  return (
    <div className="stat-tile">
      <div>
        <div className="figure">{figure}</div>
        <div className="caption">{caption}</div>
      </div>
    </div>
  )
}

// Weather alerts from the backend. Each alert says its level in words as well
// as colour, so the meaning survives a faded screen or colour blindness.
export function AlertList({ alerts, compact = false }) {
  const { t } = useApp()
  if (!alerts) return null
  if (!alerts.length) {
    return (
      <div className="alert-strip clear">
        <div>{t('noAlerts')}</div>
      </div>
    )
  }
  const levelWord = { urgent: t('urgent'), caution: t('caution'), info: '' }
  return (
    <div role="region" aria-label={t('alertsTitle')}>
      {alerts.map((alert) => (
        <div className={`alert-strip ${alert.level}`} key={alert.kind}>
          <i className={`bi bi-${alert.icon}`} aria-hidden="true" />
          <div>
            <div className="fw-bold">
              {levelWord[alert.level] ? `${levelWord[alert.level]}: ` : ''}
              {alert.title}
            </div>
            {!compact && <div className="small">{alert.text}</div>}
          </div>
        </div>
      ))}
    </div>
  )
}

// `flush` removes the gap above the footer, for pages that end on a coloured
// section of their own.
export function Footer({ flush = false }) {
  const { t, farmer } = useApp()
  return (
    <footer className="footer-mlimi" style={flush ? { marginTop: 0 } : undefined}>
      <div className="container">
        <div className="row g-4">
          <div className="col-lg-6">
            <div className="d-flex align-items-center mb-2">
              <img src="/leaf.svg" alt="" className="brand-leaf" />
              <span className="fs-5 fw-bold text-white" style={{ fontFamily: 'var(--font-head)' }}>
                MlimiSmart
              </span>
            </div>
            <p className="small mb-0">{t('tagline')}.</p>
          </div>
          <div className="col-6 col-lg-3">
            <h2>{t('navTools')}</h2>
            <ul className="small">
              <li><Link to={farmer ? '/dashboard' : '/login'}>{t('navDashboard')}</Link></li>
              <li><Link to="/calendar">{t('navCalendar')}</Link></li>
              <li><Link to="/harvest">{t('navHarvest')}</Link></li>
            </ul>
          </div>
          <div className="col-6 col-lg-3">
            <h2>{t('navPhones')}</h2>
            <ul className="small">
              <li><Link to="/ussd">USSD *384*211#</Link></li>
              <li><Link to="/sms">SMS</Link></li>
              <li><Link to="/map">{t('navMap')}</Link></li>
              <li><Link to="/about">{t('navAbout')}</Link></li>
            </ul>
          </div>
        </div>
        <div className="footer-bottom d-flex justify-content-between flex-wrap gap-2">
          <span>{t('footer')}</span>
          <Link to="/about">{t('navAbout')}</Link>
        </div>
      </div>
    </footer>
  )
}

// Guards the farmer-only screens. `booting` is respected so a page refresh
// does not bounce a logged-in farmer to the login screen while the stored
// token is still being verified.
export function RequireAuth({ children, adminOnly = false }) {
  const { farmer, isAdmin, booting } = useApp()
  if (booting) return <Spinner />
  if (!farmer) return <Navigate to="/login" replace />
  if (adminOnly && !isAdmin) return <Navigate to="/dashboard" replace />
  return children
}
