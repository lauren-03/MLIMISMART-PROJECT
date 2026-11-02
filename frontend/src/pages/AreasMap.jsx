// Map of every tea area MlimiSmart covers, with today's weather on each pin.
import L from 'leaflet'
import { useEffect, useMemo, useRef, useState } from 'react'
import { MapContainer, Marker, Popup, TileLayer, useMap } from 'react-leaflet'
import { Link } from 'react-router-dom'

import { api, errorMessage } from '../api/client'
import { ErrorBox, Footer, PageHead, Spinner } from '../components/Shared'
import { WeatherIcon } from '../components/WeatherCard'
import { useApp } from '../context/AppContext'

const CENTRE = [-16.05, 35.32]

function pinIcon(area) {
  const label = area.temperature !== null && area.temperature !== undefined
    ? `${Math.round(area.temperature)}°` : '•'
  return L.divIcon({
    className: '',
    html: `<div class="map-pin ${area.district.toLowerCase()}">${label}</div>`,
    iconSize: [40, 22],
    iconAnchor: [20, 11],
    popupAnchor: [0, -10],
  })
}

function FlyTo({ area }) {
  const map = useMap()
  useEffect(() => {
    if (area) map.flyTo([area.latitude, area.longitude], 12, { duration: 0.8 })
  }, [area, map])
  return null
}

export default function AreasMap() {
  const { language, farmer, t } = useApp()
  const [areas, setAreas] = useState(null)
  const [error, setError] = useState(null)
  const [district, setDistrict] = useState('All')
  const [selected, setSelected] = useState(null)
  const markers = useRef({})

  useEffect(() => {
    let cancelled = false
    api
      .get('/weather/areas')
      .then(({ data }) => !cancelled && setAreas(data))
      .catch((err) => !cancelled && setError(errorMessage(err, t('errorGeneric')) ?? 'network'))
    return () => {
      cancelled = true
    }
  }, [t])

  const shown = useMemo(
    () => (areas ?? []).filter((a) => district === 'All' || a.district === district),
    [areas, district],
  )

  const select = (area) => {
    setSelected(area)
    // Open the pin's popup once the map has flown there.
    setTimeout(() => markers.current[area.name]?.openPopup(), 850)
  }

  const kind = (area) => {
    const labels = {
      boma: ['District headquarters', 'Boma'], trading_centre: ['Trading centre', 'Msika'],
      research_station: ['Research station', 'Malo ofufuza'], estate: ['Tea estate area', 'Dera la esiteti'],
      mission: ['Mission', 'Mishoni'], border_post: ['Border area', 'Malire'],
    }[area.kind] ?? [area.kind, area.kind]
    return language === 'NY' ? labels[1] : labels[0]
  }

  return (
    <>
      <PageHead icon="geo-alt" title={t('mapTitle')} intro={t('mapIntro')} />
      <div className="container">
        <ErrorBox error={error} />
        {!areas && !error && <Spinner />}
        {areas && (
          <div className="row g-4">
            <div className="col-lg-8">
              <div className="map-frame">
                <MapContainer center={CENTRE} zoom={10} scrollWheelZoom={false}
                              style={{ height: '100%', width: '100%' }}>
                  <TileLayer
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                  />
                  <FlyTo area={selected} />
                  {shown.map((area) => (
                    <Marker
                      key={area.name}
                      position={[area.latitude, area.longitude]}
                      icon={pinIcon(area)}
                      ref={(ref) => {
                        if (ref) markers.current[area.name] = ref
                      }}
                      eventHandlers={{ click: () => setSelected(area) }}
                    >
                      <Popup>
                        <div style={{ minWidth: 170 }}>
                          <strong style={{ fontSize: '1rem' }}>{area.name}</strong>
                          <div className="small text-muted">
                            {kind(area)} · {area.district} · {area.altitude_m} m
                          </div>
                          {!area.offline && (
                            <div className="mt-1">
                              <WeatherIcon code={area.code} className="text-success me-1" />
                              {language === 'NY' ? area.condition_ny : area.condition_en}
                              <div>
                                {Math.round(area.temp_min)}° – {Math.round(area.temp_max)}°C ·{' '}
                                <span className="rain-figure">{t('rainShort')} {area.rain_probability}%</span>
                              </div>
                            </div>
                          )}
                        </div>
                      </Popup>
                    </Marker>
                  ))}
                </MapContainer>
              </div>
              <p className="small text-muted mt-2">
                <span className="map-pin d-inline-block me-1">22°</span> Thyolo
                <span className="map-pin mulanje d-inline-block ms-3 me-1">22°</span> Mulanje
              </p>
            </div>

            <div className="col-lg-4">
              <div className="btn-group w-100 mb-3" role="group" aria-label={t('district')}>
                {['All', 'Thyolo', 'Mulanje'].map((d) => (
                  <button key={d} type="button"
                          className={`btn ${district === d ? 'btn-tea' : 'btn-outline-tea'}`}
                          aria-pressed={district === d} onClick={() => setDistrict(d)}>
                    {d === 'All' ? t('allDistricts') : d}
                  </button>
                ))}
              </div>
              <div className="card card-mlimi">
                <div className="card-body p-2 area-list">
                  {shown.map((area) => (
                    <button type="button" key={area.name}
                            className={`area-row${selected?.name === area.name ? ' selected' : ''}`}
                            onClick={() => select(area)}>
                      <span>
                        <span className="fw-bold d-block">{area.name}</span>
                        <span className="small text-muted">{kind(area)} · {area.altitude_m} m</span>
                      </span>
                      {!area.offline && (
                        <span className="text-end small">
                          <WeatherIcon code={area.code} className="text-success me-1" />
                          <strong>{Math.round(area.temperature)}°</strong>
                          <span className="d-block rain-figure">
                            {t('rainShort')} {area.rain_probability}%
                          </span>
                        </span>
                      )}
                    </button>
                  ))}
                </div>
              </div>
              {!farmer && (
                <Link to="/register" className="btn btn-tea w-100 mt-3">
                  {t('getStarted')}
                </Link>
              )}
            </div>
          </div>
        )}
      </div>
      <Footer />
    </>
  )
}
