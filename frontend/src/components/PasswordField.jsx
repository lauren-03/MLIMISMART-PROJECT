// Password input with a live checklist of the strength rules.
import { useState } from 'react'

import { useApp } from '../context/AppContext'

export const PASSWORD_MIN_LENGTH = 8

const COMMON = new Set([
  'password', 'passw0rd', 'qwerty', 'abc', 'abcd', 'letmein', 'welcome', 'admin',
  'farmer', 'mlimi', 'mlimismart', 'tea', 'tiyi', 'malawi', 'thyolo', 'mulanje',
  'blantyre', 'lilongwe', 'iloveyou', 'monkey', 'football', 'secret', 'zikomo', 'moni',
  '12345678', '123456789', '1234567890', '87654321', '11111111', '00000000',
])

export function passwordChecks(password, { name = '', phone = '' } = {}) {
  const value = password || ''
  const lowered = value.toLowerCase()
  const letters = lowered.replace(/[^a-z]/g, '')
  const digits = value.replace(/\D/g, '')
  const nameParts = (name || '').toLowerCase().split(/[^a-z]+/).filter((p) => p.length >= 3)
  const phoneDigits = (phone || '').replace(/\D/g, '')

  return [
    { key: 'pwLength', ok: value.length >= PASSWORD_MIN_LENGTH },
    { key: 'pwMix', ok: /[a-z]/i.test(value) && /\d/.test(value) },
    { key: 'pwName', ok: value.length > 0 && !nameParts.some((p) => lowered.includes(p)) },
    {
      key: 'pwPhone',
      ok: value.length > 0 && !(phoneDigits && digits.length >= 6 &&
        (phoneDigits.includes(digits) || digits.includes(phoneDigits.slice(-6)))),
    },
    {
      key: 'pwCommon',
      ok: value.length > 0 && !COMMON.has(lowered) && !COMMON.has(letters) && new Set(lowered).size > 2,
    },
  ]
}

export function isStrong(password, context) {
  return passwordChecks(password, context).every((check) => check.ok)
}

export default function PasswordField({ id = 'password', label, value, onChange, name, phone, autoComplete = 'new-password' }) {
  const { t } = useApp()
  const [visible, setVisible] = useState(false)
  const checks = passwordChecks(value, { name, phone })

  return (
    <div>
      <label className="form-label" htmlFor={id}>{label ?? t('password')}</label>
      <div className="input-group">
        <input
          id={id}
          name="password"
          type={visible ? 'text' : 'password'}
          className="form-control"
          value={value}
          onChange={onChange}
          autoComplete={autoComplete}
          aria-describedby={`${id}-rules`}
          required
        />
        <button type="button" className="btn btn-outline-tea" onClick={() => setVisible((v) => !v)}>
          {visible ? t('pwHide') : t('pwShow')}
        </button>
      </div>
      <ul id={`${id}-rules`} className="password-rules" aria-live="polite">
        {checks.map((check) => (
          <li key={check.key} className={check.ok ? 'met' : ''}>
            <span className="rule-mark" aria-hidden="true">{check.ok ? '✓' : ''}</span>
            {t(check.key)}
            <span className="visually-hidden">{check.ok ? ` (${t('pwMet')})` : ` (${t('pwNotMet')})`}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}
