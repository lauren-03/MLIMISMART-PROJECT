// A real "not found" page instead of silently redirecting, so a mistyped or
// old link tells the farmer what happened and offers a way back.
import { Link } from 'react-router-dom'

import { Footer } from '../components/Shared'
import { useApp } from '../context/AppContext'

export default function NotFound() {
  const { t } = useApp()
  return (
    <>
      <div className="container py-5 text-center">
        <div className="display-1 fw-bold text-tea" style={{ fontFamily: 'var(--font-head)' }}>404</div>
        <h1 className="h2 text-tea mt-3">{t('notFoundTitle')}</h1>
        <p className="text-muted">{t('notFoundText')}</p>
        <Link to="/" className="btn btn-tea btn-lg mt-2">
          {t('backHome')}
        </Link>
      </div>
      <Footer />
    </>
  )
}
