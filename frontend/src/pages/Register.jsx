// Farmer registration (Module 1).
import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { api, errorMessage } from '../api/client'
import LanguageSelector from '../components/LanguageSelector'
import PasswordField, { isStrong } from '../components/PasswordField'
import { ErrorBox } from '../components/Shared'
import { useApp } from '../context/AppContext'

export default function Register() {
  const { register, language, t } = useApp()
  const navigate = useNavigate()
  const [areas, setAreas] = useState([])
  const [form, setForm] = useState({
    name: '',
    phone: '',
    password: '',
    location: 'Thyolo',
    language,
    farm_size_ha: '',
    years_farming: '',
  })
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    api
      .get('/weather/locations')
      .then(({ data }) => setAreas(data))
      .catch(() => setAreas([]))
  }, [])

  // Keep the form in step with the navbar language switch.
  useEffect(() => {
    setForm((previous) => ({ ...previous, language }))
  }, [language])

  const change = (event) =>
    setForm((previous) => ({ ...previous, [event.target.name]: event.target.value }))

  const submit = async (event) => {
    event.preventDefault()
    setBusy(true)
    setError(null)
    try {
      await register({
        ...form,
        farm_size_ha: form.farm_size_ha === '' ? null : Number(form.farm_size_ha),
        years_farming: form.years_farming === '' ? null : Number(form.years_farming),
      })
      navigate('/dashboard')
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
          <div className="col-md-9 col-lg-7">
            <div className="auth-card p-4 p-md-5">
              <div className="d-flex justify-content-between align-items-center mb-4">
                <h1 className="h4 text-tea mb-0">{t('registerTitle')}</h1>
                <LanguageSelector compact />
              </div>

              <ErrorBox error={error} />

              <form onSubmit={submit}>
                <div className="row g-3">
                  <div className="col-md-6">
                    <label className="form-label" htmlFor="name">
                      {t('fullName')}
                    </label>
                    <input
                      id="name"
                      name="name"
                      className="form-control"
                      value={form.name}
                      onChange={change}
                      required
                      minLength={2}
                    />
                  </div>
                  <div className="col-md-6">
                    <label className="form-label" htmlFor="phone">
                      {t('phone')}
                    </label>
                    <input
                      id="phone"
                      name="phone"
                      type="tel"
                      className="form-control"
                      placeholder="0991234567"
                      value={form.phone}
                      onChange={change}
                      required
                    />
                  </div>
                  <div className="col-md-6">
                    <PasswordField value={form.password} onChange={change}
                                   name={form.name} phone={form.phone} />
                  </div>
                  <div className="col-md-6">
                    <label className="form-label" htmlFor="location">
                      {t('location')}
                    </label>
                    <select
                      id="location"
                      name="location"
                      className="form-select"
                      value={form.location}
                      onChange={change}
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
                  <div className="col-md-6">
                    <label className="form-label" htmlFor="language">
                      {t('preferredLanguage')}
                    </label>
                    <select
                      id="language"
                      name="language"
                      className="form-select"
                      value={form.language}
                      onChange={change}
                    >
                      <option value="NY">{t('chichewa')}</option>
                      <option value="EN">{t('english')}</option>
                    </select>
                  </div>
                  <div className="col-md-3">
                    <label className="form-label" htmlFor="farm_size_ha">
                      {t('farmSize')}
                    </label>
                    <input
                      id="farm_size_ha"
                      name="farm_size_ha"
                      type="number"
                      step="0.1"
                      min="0"
                      className="form-control"
                      value={form.farm_size_ha}
                      onChange={change}
                      placeholder={t('optional')}
                    />
                  </div>
                  <div className="col-md-3">
                    <label className="form-label" htmlFor="years_farming">
                      {t('yearsFarming')}
                    </label>
                    <input
                      id="years_farming"
                      name="years_farming"
                      type="number"
                      min="0"
                      className="form-control"
                      value={form.years_farming}
                      onChange={change}
                      placeholder={t('optional')}
                    />
                  </div>
                </div>

                <button className="btn btn-tea btn-lg w-100 mt-4" type="submit"
                        disabled={busy || !isStrong(form.password, { name: form.name, phone: form.phone })}>
                  {busy ? t('loading') : t('register')}
                </button>
              </form>

              <p className="text-center mt-4 mb-0">
                <Link to="/login" className="text-tea">
                  {t('haveAccountQ')}
                </Link>
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
