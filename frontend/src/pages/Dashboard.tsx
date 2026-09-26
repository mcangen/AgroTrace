import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'

import { api } from '../lib/api'
import { useAuth } from '../lib/auth'
import { EventTimeline, EventTypeBars } from '../components/charts'
import OnboardingChecklist from '../components/OnboardingChecklist'
import { ErrorNote, Spinner } from '../components/ui'
import {
  AGENT_LABELS,
  EVENT_ICONS,
  EVENT_LABELS,
  formatNumber,
  formatRelative,
} from '../lib/format'

function Kpi({
  label,
  value,
  unit,
  foot,
}: {
  label: string
  value: string
  unit?: string
  foot?: string
}) {
  return (
    <div className="kpi">
      <span className="kpi-label">{label}</span>
      <span className="kpi-value">
        {value}
        {unit && <span className="kpi-unit">{unit}</span>}
      </span>
      {foot && <span className="kpi-foot">{foot}</span>}
    </div>
  )
}

export default function Dashboard() {
  const { user } = useAuth()
  const { data, isLoading, error } = useQuery({
    queryKey: ['dashboard'],
    queryFn: api.dashboard,
  })

  if (isLoading) return <Spinner label="Cargando tu panel…" />
  if (error) return <ErrorNote error={error} />
  if (!data) return null

  const firstName = user?.full_name.split(' ')[0] ?? ''
  const allValid = data.chains_broken === 0

  return (
    <div className="stack stack-6">
      <header className="page-head">
        <div>
          <span className="eyebrow">Panel de operación</span>
          <h1 className="display display-lg" style={{ marginTop: 'var(--sp-2)' }}>
            Buen día, {firstName}
          </h1>
        </div>
        <Link to="/panel/lotes/nuevo" className="btn btn-primary">
          + Registrar lote
        </Link>
      </header>

      <OnboardingChecklist summary={data} />

      {data.product_count > 0 && (
        <>
          <section className="kpi-grid">
            <Kpi
              label="Lotes"
              value={formatNumber(data.product_count)}
              foot={`en ${formatNumber(data.farm_count)} ${
                data.farm_count === 1 ? 'finca' : 'fincas'
              }`}
            />
            <Kpi
              label="Eventos sellados"
              value={formatNumber(data.event_count)}
              foot="en la cadena SHA-256"
            />
            <Kpi
              label="Integridad"
              value={`${formatNumber(data.chains_valid)}/${formatNumber(data.product_count)}`}
              foot={allValid ? '✓ todas las cadenas íntegras' : '✕ hay cadenas alteradas'}
            />
            <Kpi
              label="Reputación media"
              value={data.avg_reputation.toFixed(1)}
              unit="/5"
              foot="sube con cada evento registrado"
            />
            <Kpi
              label="Ejecuciones de IA"
              value={formatNumber(data.ai_runs)}
              foot={
                data.ai_runs > 0
                  ? `${Math.round(data.ai_success_rate * 100)}% con modelo activo`
                  : 'aún sin ejecuciones'
              }
            />
          </section>

          <section className="chart-grid">
            <EventTimeline data={data.events_last_30_days} />
            <EventTypeBars data={data.events_by_type} />
          </section>

          <section className="chart-grid">
            <div className="card card-pad">
              <div className="card-head">
                <div>
                  <h2 className="chart-title">Actividad reciente</h2>
                  <p className="chart-sub">Últimos eventos sellados en tus lotes</p>
                </div>
                <Link to="/panel/lotes" className="btn btn-ghost btn-sm">
                  Ver lotes
                </Link>
              </div>

              {data.recent_events.length === 0 ? (
                <p className="muted small">Sin eventos todavía.</p>
              ) : (
                <div className="table-scroll">
                  <table className="table">
                    <thead>
                      <tr>
                        <th scope="col">Evento</th>
                        <th scope="col">Registrado por</th>
                        <th scope="col">Cuándo</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.recent_events.map((event) => (
                        <tr key={event.id}>
                          <td>
                            <span aria-hidden="true" style={{ marginRight: 8 }}>
                              {EVENT_ICONS[event.event_type] ?? '◆'}
                            </span>
                            {EVENT_LABELS[event.event_type] ?? event.event_type}
                          </td>
                          <td className="muted">{event.recorded_by ?? '—'}</td>
                          <td className="muted">{formatRelative(event.occurred_at)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            <div className="card card-pad">
              <div className="card-head">
                <div>
                  <h2 className="chart-title">Agentes de IA</h2>
                  <p className="chart-sub">Últimas ejecuciones sobre tus lotes</p>
                </div>
              </div>

              {data.recent_agent_runs.length === 0 ? (
                <p className="muted small">
                  Aún no has ejecutado ningún agente. Abre un lote y genera su narrativa o su
                  ficha de exportación.
                </p>
              ) : (
                <div className="stack stack-3">
                  {data.recent_agent_runs.map((run) => (
                    <div className="row row-between" key={run.id}>
                      <div style={{ minWidth: 0 }}>
                        <div className="small" style={{ fontWeight: 600 }}>
                          {AGENT_LABELS[run.agent]}
                        </div>
                        <div className="small faint">
                          {run.model ?? 'sin modelo'}
                          {run.latency_ms ? ` · ${formatNumber(run.latency_ms)} ms` : ''}
                          {` · ${formatRelative(run.created_at)}`}
                        </div>
                      </div>
                      <span
                        className={`badge ${
                          run.status === 'OK'
                            ? 'badge-ok'
                            : run.status === 'FALLBACK'
                              ? 'badge-warn'
                              : 'badge-danger'
                        }`}
                      >
                        {run.status === 'OK'
                          ? '✓ Modelo'
                          : run.status === 'FALLBACK'
                            ? '◌ Respaldo'
                            : '✕ Error'}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </section>
        </>
      )}
    </div>
  )
}
