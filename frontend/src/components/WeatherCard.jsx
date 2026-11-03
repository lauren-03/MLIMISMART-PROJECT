// Live weather panel (Module 2). Shows the figures the advisory engine itself
// uses, so a farmer can see the reason behind the advice, not just the advice.
import { useApp } from '../context/AppContext'

// Map a WMO weather code to a Bootstrap Icons name. Ranges follow the
// Open-Meteo code table.
export function weatherIconName(code) {
  if (code === null || code === undefined) return 'cloud'
  if (code === 0) return 'sun'
  if (code === 1) return 'brightness-high'
  if (code === 2) return 'cloud-sun'
  if (code === 3) return 'clouds'
  if (code === 45 || code === 48) return 'cloud-fog2'
  if (code >= 95) return 'cloud-lightning-rain'
  if (code >= 80) return 'cloud-rain-heavy'
  if (code >= 61) return 'cloud-rain'
  if (code >= 51) return 'cloud-drizzle'
  return 'cloud'
}

// Colour for each kind of weather: amber sun, grey-blue cloud, blue rain.
export function weatherTone(code) {
  if (code === 0 || code === 1) return 'sun'
  if (code === 2) return 'part'
  if (code >= 95) return 'storm'
  if (code >= 51) return 'rain'
  return 'cloud'
}

export function WeatherIcon({ code, className = '' }) {
  return (
    <i className={`bi bi-${weatherIconName(code)} tone-${weatherTone(code)} ${className}`} aria-hidden="true" />
  )
}

const value = (v, unit = '') => (v === null || v === undefined ? '--' : `${v}${unit}`)

export default function WeatherCard({ weather }) {
  const { language, t } = useApp()

  if (!weather) return null

  const current = weather.current
  const condition = language === 'NY' ? current.condition_ny : current.condition_en
  const temp = current.temperature === null || current.temperature === undefined
    ? '--' : Math.round(current.temperature)

  return (
    <div className="wx-card">
      {weather.offline && (
        <div className="alert alert-warning mb-3" role="alert">
          {t('weatherOffline')}
        </div>
      )}

      <div className="d-flex justify-content-between align-items-start gap-3">
        <div>
          <div className="wx-place">
            {t('today')} · {weather.location}
            {weather.district && weather.district !== weather.location && (
              <span className="text-muted">, {weather.district}</span>
            )}
          </div>
          <div className="d-flex align-items-end gap-3 my-1">
            <span className="wx-temp">{temp}°</span>
            <span className="wx-condition">{condition}</span>
          </div>
        </div>
        <WeatherIcon code={current.code} className="wx-big" />
      </div>

      <div className="wx-facts">
        {current.rain_probability === null && current.rain_today_mm !== null ? (
          <span>{t('rainToday')} <strong>{value(current.rain_today_mm, ' mm')}</strong></span>
        ) : (
          <span>{t('rainChance')} <strong>{value(current.rain_probability, '%')}</strong></span>
        )}
        <span>{t('humidity')} <strong>{value(current.humidity, '%')}</strong></span>
        <span>{t('wind')} <strong>{value(current.wind_kph, ' km/h')}</strong></span>
      </div>

      {weather.stale && (
        <div className="wx-updated">{t('lastUpdated')} {timeAgo(weather.observed_at, t)}</div>
      )}
    </div>
  )
}

function timeAgo(iso, t) {
  const minutes = Math.max(0, Math.round((Date.now() - new Date(iso).getTime()) / 60000))
  if (minutes < 1) return t('justNow')
  if (minutes < 60) return `${t('updated')} ${minutes} min`
  return `${t('updated')} ${Math.round(minutes / 60)} h`
}
