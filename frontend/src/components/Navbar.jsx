// Site navigation.
import { useEffect, useRef, useState } from 'react'
import { Link, NavLink, useLocation, useNavigate } from 'react-router-dom'

import { useApp } from '../context/AppContext'
import LanguageSelector from './LanguageSelector'

function Dropdown({ label, icon, items, onNavigate }) {
  const [open, setOpen] = useState(false)
  const ref = useRef(null)
  const location = useLocation()
  const active = items.some((item) => location.pathname.startsWith(item.to))

  useEffect(() => {
    const close = (event) => {
      if (ref.current && !ref.current.contains(event.target)) setOpen(false)
    }
    const escape = (event) => {
      if (event.key === 'Escape') setOpen(false)
    }
    document.addEventListener('mousedown', close)
    document.addEventListener('keydown', escape)
    return () => {
      document.removeEventListener('mousedown', close)
      document.removeEventListener('keydown', escape)
    }
  }, [])

  return (
    <li className="nav-item nav-dropdown" ref={ref}>
      <button
        type="button"
        className={`nav-link btn btn-link border-0${active ? ' active' : ''}`}
        aria-expanded={open}
        onClick={() => setOpen((value) => !value)}
      >
        {label}
        <i className={`bi bi-chevron-${open ? 'up' : 'down'} small`} aria-hidden="true" />
      </button>
      {open && (
        <ul className="nav-dropdown-menu">
          {items.map((item) => (
            <li key={item.to}>
              <NavLink
                to={item.to}
                onClick={() => {
                  setOpen(false)
                  onNavigate()
                }}
              >
                {item.label}
              </NavLink>
            </li>
          ))}
        </ul>
      )}
    </li>
  )
}

export default function Navbar() {
  const { farmer, isAdmin, logout, t } = useApp()
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)

  const close = () => setOpen(false)

  const handleLogout = () => {
    logout()
    close()
    navigate('/')
  }

  const linkClass = ({ isActive }) => `nav-link${isActive ? ' active' : ''}`

  const tools = [
    { to: '/calendar', icon: 'calendar3', label: t('navCalendar') },
    { to: '/harvest', icon: 'basket', label: t('navHarvest') },
    { to: '/history', icon: 'clock-history', label: t('navHistory') },
    { to: '/map', icon: 'geo-alt', label: t('navMap') },
  ]
  const phones = [
    { to: '/ussd', icon: 'telephone', label: t('navUssd') },
    { to: '/sms', icon: 'chat-dots', label: t('navSms') },
  ]

  return (
    <nav className="navbar navbar-expand-xl navbar-mlimi sticky-top" aria-label="Main">
      <div className="container">
        <Link className="navbar-brand d-flex align-items-center" to="/" onClick={close}>
          <img src="/leaf.svg" alt="" className="brand-leaf" />
          Mlimi<span>Smart</span>
        </Link>

        <button
          className="navbar-toggler"
          type="button"
          onClick={() => setOpen((value) => !value)}
          aria-expanded={open}
          aria-controls="main-nav"
          aria-label="Toggle navigation"
        >
          <span className="navbar-toggler-icon" />
        </button>

        <div id="main-nav" className={`collapse navbar-collapse${open ? ' show' : ''}`}>
          <ul className="navbar-nav me-auto gap-xl-1">
            {farmer ? (
              <>
                <li className="nav-item">
                  <NavLink to="/dashboard" className={linkClass} onClick={close}>
                    {t('navDashboard')}
                  </NavLink>
                </li>
                <li className="nav-item">
                  <NavLink to="/weather" className={linkClass} onClick={close}>
                    {t('navWeather')}
                  </NavLink>
                </li>
                <li className="nav-item">
                  <NavLink to="/ask" className={linkClass} onClick={close}>
                    {t('navAsk')}
                  </NavLink>
                </li>
                <Dropdown label={t('navTools')} icon="grid" items={tools} onNavigate={close} />
              </>
            ) : (
              <>
                <li className="nav-item">
                  <NavLink to="/" className={linkClass} onClick={close} end>
                    {t('navHome')}
                  </NavLink>
                </li>
                <li className="nav-item">
                  <NavLink to="/map" className={linkClass} onClick={close}>
                    {t('navMap')}
                  </NavLink>
                </li>
                <li className="nav-item">
                  <NavLink to="/calendar" className={linkClass} onClick={close}>
                    {t('navCalendar')}
                  </NavLink>
                </li>
              </>
            )}
            <Dropdown label={t('navPhones')} icon="phone" items={phones} onNavigate={close} />
            <li className="nav-item">
              <NavLink to="/about" className={linkClass} onClick={close}>
                {t('navAbout')}
              </NavLink>
            </li>
            {isAdmin && (
              <li className="nav-item">
                <NavLink to="/admin" className={linkClass} onClick={close}>
                  {t('navAdmin')}
                </NavLink>
              </li>
            )}
          </ul>

          <div className="d-flex align-items-center gap-2 flex-wrap flex-xl-nowrap py-2 py-xl-0">
            <LanguageSelector />
            {farmer ? (
              <>
                <NavLink to="/profile" className="nav-link" onClick={close}>
                  {farmer.name.split(' ')[0]}
                </NavLink>
                <button className="btn btn-sm btn-outline-tea" onClick={handleLogout}>
                  {t('logout')}
                </button>
              </>
            ) : (
              <>
                <Link to="/login" className="btn btn-sm btn-outline-tea" onClick={close}>
                  {t('login')}
                </Link>
                <Link to="/register" className="btn btn-sm btn-tea" onClick={close}>
                  {t('register')}
                </Link>
              </>
            )}
          </div>
        </div>
      </div>
    </nav>
  )
}
