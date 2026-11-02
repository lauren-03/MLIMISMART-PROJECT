// The five day outlook, with the chance of rain for each day.
import { useApp } from '../context/AppContext'
import { WeatherIcon } from './WeatherCard'

export default function ForecastStrip({ forecast }) {
  const { language, t } = useApp()

  if (!forecast?.length) return null

  return (
    <div className="wx-card mt-4">
      <div className="wx-divider"><span>{t('forecast5')}</span></div>
      <div className="wx-days">
        {forecast.map((day) => (
          <div className="wx-day" key={day.date}>
            <div className="wx-dayname">{day.weekday}</div>
            <WeatherIcon code={day.code} className="wx-dayicon" />
            <div className="wx-max">{Math.round(day.temp_max)}°</div>
            <div className="wx-min">{Math.round(day.temp_min)}°</div>
            <div className="wx-rain">{t('rainShort')} {day.rain_probability}%</div>
            <div className="wx-cond d-none d-md-block">
              {language === 'NY' ? day.condition_ny : day.condition_en}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
