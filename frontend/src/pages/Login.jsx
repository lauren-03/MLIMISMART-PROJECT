import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { errorMessage } from '../api/client'
import LanguageSelector from '../components/LanguageSelector'
import { ErrorBox } from '../components/Shared'
import { useApp } from '../context/AppContext'

export default function Login() {
  const { login, t } = useApp()
  const navigate = useNavigate()
  const [form, setForm] = useState({ phone: '', password: '' })
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)

  const change = (event) =>
    setForm((previous) => ({ ...previous, [event.target.name]: event.target.value }))

  const submit = async (event) => {
    event.preventDefault()
    setBusy(true)
    setError(null)
    try {
      const farmer = await login(form.phone, form.password)
      navigate(farmer.role === 'ADMIN' ? '/admin' : '/dashboard')
    } catch (err) {
      setError(errorMessage(err, t('errorGeneric')) ?? 'network')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="auth-shell">
      <div className="container">
        <div className="row justify-content-center">
          <div className="col-md-7 col-lg-5">
            <div className="auth-card p-4 p-md-5">
              <div className="d-flex justify-content-between align-items-center mb-4">
                <h1 className="h4 text-tea mb-0">{t('loginTitle')}</h1>
                <div className="bg-dark rounded p-1">
                  <LanguageSelector compact />
                </div>
              </div>

              <ErrorBox error={error} />

              <form onSubmit={submit}>
                <div className="mb-3">
                  <label className="form-label" htmlFor="phone">
                    {t('phone')}
                  </label>
                  <input
                    id="phone"
                    name="phone"
                    type="tel"
                    className="form-control form-control-lg"
                    placeholder="0991234567"
                    value={form.phone}
                    onChange={change}
                    required
                    autoComplete="tel"
                  />
                </div>
                <div className="mb-4">
                  <label className="form-label" htmlFor="password">
                    {t('password')}
                  </label>
                  <input
                    id="password"
                    name="password"
                    type="password"
                    className="form-control form-control-lg"
                    value={form.password}
                    onChange={change}
                    required
                    autoComplete="current-password"
                  />
                </div>
                <button className="btn btn-tea btn-lg w-100" type="submit" disabled={busy}>
                  {busy ? t('loading') : t('login')}
                </button>
              </form>

              <p className="text-center mt-4 mb-0">
                <Link to="/register" className="text-tea">
                  {t('noAccount')}
                </Link>
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
