// English / Chichewa switch (Module 5: Language).
import { useEffect, useRef, useState } from 'react'

import { useApp } from '../context/AppContext'

const NAMES = {
  EN: { EN: 'English', NY: 'Chichewa' },
  NY: { EN: 'Chingerezi (English)', NY: 'Chichewa' },
}

export default function LanguageSelector({ compact = false }) {
  const { language, changeLanguage, t } = useApp()
  const [open, setOpen] = useState(false)
  const box = useRef(null)

  useEffect(() => {
    if (!open) return undefined
    const close = (event) => {
      if (event.key === 'Escape' || (event.type === 'mousedown' && !box.current?.contains(event.target))) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', close)
    document.addEventListener('keydown', close)
    return () => {
      document.removeEventListener('mousedown', close)
      document.removeEventListener('keydown', close)
    }
  }, [open])

  const names = NAMES[language]
  const choose = (code) => {
    changeLanguage(code)
    setOpen(false)
  }

  return (
    <div className="lang-menu" ref={box}>
      <button
        type="button"
        className="lang-toggle"
        aria-haspopup="true"
        aria-expanded={open}
        onClick={() => setOpen((value) => !value)}
      >
        <i className="bi bi-globe2" aria-hidden="true" />
        <span>{compact ? language : t('language')}</span>
        <i className="bi bi-chevron-down small" aria-hidden="true" />
      </button>
      {open && (
        <div className="lang-popover" role="menu">
          <div className="lang-current">
            {t('currentLanguage')}: {names[language]}
          </div>
          {['EN', 'NY'].map((code) => (
            <button
              key={code}
              type="button"
              role="menuitemradio"
              aria-checked={language === code}
              className={`lang-option${language === code ? ' active' : ''}`}
              onClick={() => choose(code)}
            >
              {names[code]}
              {language === code && <i className="bi bi-check2" aria-hidden="true" />}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
