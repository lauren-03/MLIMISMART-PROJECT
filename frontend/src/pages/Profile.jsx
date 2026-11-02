// Farmer profile. Changing the area or language here also changes what the
// farmer receives by SMS, because the backend reads the same record.
import { useEffect, useState } from 'react'

import { api, errorMessage } from '../api/client'
import PasswordField, { isStrong } from '../components/PasswordField'
import { ErrorBox, Footer, PageHeader } from '../components/Shared'
import { useApp } from '../context/AppContext'

// Change password: the new password must pass the same rules as at
// registration, so a farmer who registered before the rules existed can move
// to a strong one.
function ChangePassword() {
  const { farmer, t } = useApp()
  const [current, setCurrent] = useState('')
  const [next, setNext] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const [done, setDone] = useState(false)

  const submit = async (event) => {
    event.preventDefault()
    setBusy(true)
    setError(null)
    setDone(false)
    try {
      await api.post('/auth/password', { current_password: current, new_password: next })
      setDone(true)
      setCurrent('')
      setNext('')
    } catch (err) {
      setError(errorMessage(err, t('errorGeneric')) ?? 'network')
    } finally {
      setBusy(false)
    }
  }

  return (
    <form className="card card-mlimi" onSubmit={submit}>
      <div className="card-body">
        <h2 className="h5 text-tea">{t('pwChangeTitle')}</h2>
        <ErrorBox error={error} />
        {done && <div className="alert alert-success" role="status">{t('pwChanged')}</div>}
        <div className="mb-3">
          <label className="form-label" htmlFor="current-password">{t('pwCurrent')}</label>
          <input id="current-password" type="password" className="form-control" required
                 autoComplete="current-password" value={current}
                 onChange={(e) => setCurrent(e.target.value)} />
        </div>
        <PasswordField id="new-password" label={t('pwNew')} value={next}
                       onChange={(e) => setNext(e.target.value)}
                       name={farmer.name} phone={farmer.phone} />
        <button className="btn btn-tea mt-3" disabled={busy || !current || !isStrong(next, farmer)}>
          {t('pwChangeButton')}
        </button>
      </div>
    </form>
  )
}

export default function Profile() {
  const { farmer, updateFarmer, t } = useApp()
  const [areas, setAreas] = useState([])
  const [form, setForm] = useState({
    name: farmer.name,
    location: farmer.location,
    language: farmer.language,
    farm_size_ha: farmer.farm_size_ha ?? '',
    years_farming: farmer.years_farming ?? '',
  })
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    api
      .get('/weather/locations')
      .then(({ data }) => setAreas(data))
      .catch(() => setAreas([]))
  }, [])

  const change = (event) => {
    setSaved(false)
    setForm((previous) => ({ ...previous, [event.target.name]: event.target.value }))
  }

  const submit = async (event) => {
    event.preventDefault()
    setBusy(true)
    setError(null)
    try {
      const { data } = await api.patch('/auth/me', {
        ...form,
        farm_size_ha: form.farm_size_ha === '' ? null : Number(form.farm_size_ha),
        years_farming: form.years_farming === '' ? null : Number(form.years_farming),
      })
      updateFarmer(data)
      setSaved(true)
    } catch (err) {
      setError(errorMessage(err, t('errorGeneric')) ?? 'network')
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <div className="container py-4">
        <PageHeader title={t('profileTitle')} subtitle={farmer.phone} />

        <div className="row g-4">
          <div className="col-lg-7">
            <div className="card card-mlimi">
              <div className="card-body">
                <ErrorBox error={error} />
                {saved && <div className="alert alert-success">{t('saved')}</div>}

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
                      />
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
                      />
                    </div>
                  </div>

                  <button className="btn btn-tea mt-4" type="submit" disabled={busy}>
                    {busy ? t('loading') : t('saveChanges')}
                  </button>
                </form>
              </div>
            </div>
          </div>
          <div className="col-lg-5">
            <ChangePassword />
            <img
              src="/images/farmer-portrait.jpg"
              alt="A tea farmer holding a freshly plucked shoot"
              className="section-photo mt-4"
              style={{ maxHeight: 280 }}
            />
          </div>
        </div>
      </div>
      <Footer />
    </>
  )
}
