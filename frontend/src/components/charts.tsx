/** Gráficas del panel.
 *
 * Decisiones de forma: la actividad en el tiempo es una serie única, así que va
 * como área con línea fina y crosshair, sin leyenda (el título la nombra). El
 * desglose por tipo de evento es magnitud por categoría: barras horizontales de
 * un solo tono con etiqueta directa del valor, de modo que la identidad nunca
 * depende del color. Ambas exponen los datos en tabla.
 */

import { useState } from 'react'
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import type { EventTypeSlice, TimelinePoint } from '../lib/types'
import { EVENT_LABELS, formatNumber } from '../lib/format'
import type { EventType } from '../lib/types'

const SERIES = '#2a7d48'
const GRID = 'rgba(18, 52, 31, 0.08)'
const AXIS = '#8a978e'

function shortDay(iso: string): string {
  const date = new Date(`${iso}T00:00:00`)
  return new Intl.DateTimeFormat('es-CO', { day: 'numeric', month: 'short' }).format(date)
}

function TimelineTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean
  payload?: Array<{ value?: number }>
  label?: string
}) {
  if (!active || !payload?.length) return null
  const value = payload[0]?.value ?? 0
  return (
    <div className="chart-tooltip">
      <div className="chart-tooltip-label">{label ? shortDay(label) : ''}</div>
      <div className="chart-tooltip-value">
        {formatNumber(value)} {value === 1 ? 'evento' : 'eventos'}
      </div>
    </div>
  )
}

function DataToggle({ open, onToggle }: { open: boolean; onToggle: () => void }) {
  return (
    <button
      type="button"
      className="btn btn-ghost btn-sm"
      onClick={onToggle}
      aria-expanded={open}
    >
      {open ? 'Ocultar datos' : 'Ver datos'}
    </button>
  )
}

export function EventTimeline({ data }: { data: TimelinePoint[] }) {
  const [showTable, setShowTable] = useState(false)
  const total = data.reduce((sum, point) => sum + point.count, 0)
  const withActivity = data.filter((point) => point.count > 0)

  return (
    <section className="card card-pad">
      <div className="card-head">
        <div>
          <h2 className="chart-title">Actividad de registro</h2>
          <p className="chart-sub">
            {formatNumber(total)} eventos sellados en los últimos 30 días
          </p>
        </div>
        <DataToggle open={showTable} onToggle={() => setShowTable((v) => !v)} />
      </div>

      <div style={{ height: 220, margin: '0 -8px' }}>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 8, right: 12, bottom: 0, left: -18 }}>
            <defs>
              <linearGradient id="timelineFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={SERIES} stopOpacity={0.22} />
                <stop offset="100%" stopColor={SERIES} stopOpacity={0.02} />
              </linearGradient>
            </defs>
            <CartesianGrid stroke={GRID} vertical={false} />
            <XAxis
              dataKey="date"
              tickFormatter={shortDay}
              tick={{ fill: AXIS, fontSize: 11 }}
              tickLine={false}
              axisLine={false}
              interval="preserveStartEnd"
              minTickGap={44}
            />
            <YAxis
              allowDecimals={false}
              width={44}
              tick={{ fill: AXIS, fontSize: 11 }}
              tickLine={false}
              axisLine={false}
            />
            <Tooltip
              content={<TimelineTooltip />}
              cursor={{ stroke: SERIES, strokeWidth: 1, strokeDasharray: '3 3' }}
            />
            <Area
              type="monotone"
              dataKey="count"
              stroke={SERIES}
              strokeWidth={2}
              fill="url(#timelineFill)"
              activeDot={{ r: 4, fill: SERIES, stroke: '#fff', strokeWidth: 2 }}
              dot={false}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {showTable && (
        <div className="table-scroll" style={{ marginTop: 'var(--sp-4)', maxHeight: 220 }}>
          <table className="table">
            <caption className="sr-only">Eventos registrados por día</caption>
            <thead>
              <tr>
                <th scope="col">Día</th>
                <th scope="col">Eventos</th>
              </tr>
            </thead>
            <tbody>
              {withActivity.length === 0 ? (
                <tr>
                  <td colSpan={2} className="muted">
                    Sin eventos en los últimos 30 días.
                  </td>
                </tr>
              ) : (
                withActivity.map((point) => (
                  <tr key={point.date}>
                    <td>{shortDay(point.date)}</td>
                    <td className="tnum">{formatNumber(point.count)}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}

export function EventTypeBars({ data }: { data: EventTypeSlice[] }) {
  const max = Math.max(1, ...data.map((slice) => slice.count))

  return (
    <section className="card card-pad">
      <div className="card-head">
        <div>
          <h2 className="chart-title">Eventos por etapa</h2>
          <p className="chart-sub">Distribución histórica de toda la operación</p>
        </div>
      </div>

      {data.length === 0 ? (
        <p className="muted small">Aún no hay eventos registrados.</p>
      ) : (
        <div className="bar-rows">
          {data.map((slice) => {
            const label =
              EVENT_LABELS[slice.event_type as EventType] ?? slice.event_type
            return (
              <div className="bar-row" key={slice.event_type}>
                <span className="bar-row-label">{label}</span>
                <span className="bar-row-value">{formatNumber(slice.count)}</span>
                <div
                  className="bar-track"
                  role="img"
                  aria-label={`${label}: ${slice.count} eventos`}
                >
                  <div
                    className="bar-fill"
                    style={{ width: `${(slice.count / max) * 100}%` }}
                  />
                </div>
              </div>
            )
          })}
        </div>
      )}
    </section>
  )
}
