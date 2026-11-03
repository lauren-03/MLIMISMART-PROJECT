// Routing for the MlimiSmart web application.
import { Suspense, lazy, useEffect } from 'react'
import { Route, Routes, useLocation } from 'react-router-dom'

import Navbar from './components/Navbar'
import { RequireAuth, Spinner } from './components/Shared'
import { useApp } from './context/AppContext'
import About from './pages/About'
import Ask from './pages/Ask'
import Calendar from './pages/Calendar'
import Dashboard from './pages/Dashboard'
import History from './pages/History'
import Home from './pages/Home'
import Login from './pages/Login'
import NotFound from './pages/NotFound'
import Profile from './pages/Profile'
import Register from './pages/Register'
import SmsPage from './pages/SmsPage'
import UssdPage from './pages/UssdPage'
import Weather from './pages/Weather'

// The map (Leaflet) and the chart pages (Recharts) are the heaviest code, so
// they load only when opened. The home page arrives faster on a slow
// rural connection.
const Admin = lazy(() => import('./pages/Admin'))
const AreasMap = lazy(() => import('./pages/AreasMap'))
const Harvest = lazy(() => import('./pages/Harvest'))

const guarded = (element, adminOnly = false) => (
  <RequireAuth adminOnly={adminOnly}>{element}</RequireAuth>
)

export default function App() {
  const { pathname } = useLocation()
  const { language, t } = useApp()

  // Each new page starts at the top, and the document language follows the
  // interface language so screen readers pronounce it correctly.
  useEffect(() => {
    window.scrollTo(0, 0)
  }, [pathname])
  useEffect(() => {
    document.documentElement.lang = language === 'NY' ? 'ny' : 'en'
  }, [language])

  return (
    <>
      <a href="#main" className="skip-link">{t('skipToContent')}</a>
      <Navbar />
      <main id="main" tabIndex={-1}>
        <Suspense fallback={<Spinner />}>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/sms" element={<SmsPage />} />
            <Route path="/ussd" element={<UssdPage />} />
            <Route path="/map" element={<AreasMap />} />
            <Route path="/calendar" element={<Calendar />} />
            <Route path="/about" element={<About />} />

            <Route path="/dashboard" element={guarded(<Dashboard />)} />
            <Route path="/weather" element={guarded(<Weather />)} />
            <Route path="/ask" element={guarded(<Ask />)} />
            <Route path="/history" element={guarded(<History />)} />
            <Route path="/profile" element={guarded(<Profile />)} />
            <Route path="/harvest" element={guarded(<Harvest />)} />
            <Route path="/admin" element={guarded(<Admin />, true)} />

            <Route path="*" element={<NotFound />} />
          </Routes>
        </Suspense>
      </main>
    </>
  )
}
