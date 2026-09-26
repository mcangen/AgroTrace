/** Pronóstico y alertas climáticas de una finca.
 *
 * Se carga bajo demanda (al desplegar el panel), no con la lista de fincas:
 * es una llamada a un servicio externo y no tiene por qué retrasar la pantalla.
 */

import { useQuery } from '@tanstack/react-query'

import { api } from '../lib/api'
import { ErrorNote, Spinner } from '../components/ui'

const SEVERITY_BADGE: Record<string, { cls: string; label: string }> = {
  riesgo: { cls: 'badge-danger', label: 'Riesgo' },
  aviso: { cls: 'badge-warn', label: 'Aviso' },
  info: { cls: 'badge-ok', label: 'Todo bien' },
}

function dayLabel(iso: string): string {
  const date = new Date(`${iso}T00:00:00`)
  return new Intl.DateTimeFormat('es-CO', { weekday: 'short', day: 'numeric' }).format(date)
}

export default function WeatherPanel({ farmId }: { farmId: number }) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['weather', farmId],
    queryFn: () => api.farmWeather(farmId),
    // El pronóstico no cambia minuto a minuto; evita recargas innecesarias.
    staleTime: 30 * 60_000,
    retry: false,
  })

  if (isLoading) return <Spinner label="Consultando el clima…" />
  if (error) return <ErrorNote error={error} />
  if (!data) return null

  return (
    <div className="stack stack-4">
      <div className="weather-days">
        {data.days.map((day) => (
          <div className="weather-day" key={day.date}>
            <div className="weather-day-label">{dayLabel(day.date)}</div>
            <div className="weather-day-temp">
              {day.temp_max != null ? Math.round(day.temp_max) : '—'}°
              <span className="weather-day-min">
                {day.temp_min != null ? Math.round(day.temp_min) : '—'}°
              </span>
            </div>
            <div className="weather-day-rain">
              💧 {day.precipitation_probability ?? 0}%
              {day.precipitation_mm != null && day.precipitation_mm > 0 && (
                <span className="faint"> · {day.precipitation_mm.toFixed(1)} mm</span>
              )}
            </div>
          </div>
        ))}
      </div>

      <div>
        {data.alerts.map((alert, index) => {
          const badge = SEVERITY_BADGE[alert.severity] ?? SEVERITY_BADGE.info
          return (
            <div className="insight" key={index}>
              <span className={`badge ${badge.cls}`}>{badge.label}</span>
              <div>
                <div className="insight-title">{alert.title}</div>
                <p className="insight-detail">{alert.detail}</p>
              </div>
            </div>
          )
        })}
      </div>

      <p className="small faint">
        Datos de Open-Meteo · {data.location} ({data.latitude.toFixed(3)},{' '}
        {data.longitude.toFixed(3)})
      </p>
    </div>
  )
}
