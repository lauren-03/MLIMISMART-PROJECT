// Area picker grouped by district, used wherever a farmer chooses where they farm.
import { useEffect, useState } from 'react'

import { api } from '../api/client'

let cache = null

export function useAreas() {
  const [areas, setAreas] = useState(cache ?? [])
  useEffect(() => {
    if (cache) return
    let cancelled = false
    api
      .get('/weather/locations')
      .then(({ data }) => {
        cache = data
        if (!cancelled) setAreas(data)
      })
      .catch(() => {})
    return () => {
      cancelled = true
    }
  }, [])
  return areas
}

export default function AreaSelect({ id = 'area', value, onChange, className = 'form-select', ...rest }) {
  const areas = useAreas()
  const districts = [...new Set(areas.map((a) => a.district))]

  return (
    <select
      id={id}
      className={className}
      value={value}
      onChange={(event) => onChange(event.target.value)}
      {...rest}
    >
      {!areas.length && <option value={value}>{value}</option>}
      {districts.map((district) => (
        <optgroup key={district} label={`${district} District`}>
          {areas
            .filter((a) => a.district === district)
            .map((a) => (
              <option key={a.name} value={a.name}>
                {a.kind === 'boma' ? `${a.name} Boma` : a.name}
              </option>
            ))}
        </optgroup>
      ))}
    </select>
  )
}
