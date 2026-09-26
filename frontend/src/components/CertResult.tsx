/** Resultado de un diagnóstico de certificación: veredicto, puntaje, brechas
 * críticas, puntaje por sección y la hoja de ruta (del modelo o de respaldo). */

import { useMutation, useQueryClient } from '@tanstack/react-query'

import { api } from '../lib/api'
import type { CertificationAssessment } from '../lib/types'
import { AiBadge, ErrorNote } from './ui'
import { CERT_VERDICT_LABELS } from '../lib/format'

const VERDICT_STYLE: Record<string, { cls: string; icon: string }> = {
  READY: { cls: 'badge-ok', icon: '🎉' },
  ALMOST_READY: { cls: 'badge-warn', icon: '📋' },
  NOT_READY: { cls: 'badge-danger', icon: '⚠' },
}

function priorityBadge(priority: string): { cls: string; label: string } {
  const p = priority.toLowerCase()
  if (p.includes('crit')) return { cls: 'badge-danger', label: 'Crítico' }
  if (p.includes('alto')) return { cls: 'badge-warn', label: 'Alto' }
  return { cls: 'badge-info', label: 'Medio' }
}

export default function CertResult({
  assessment,
  productId,
  publicId,
  published,
  onRetry,
}: {
  assessment: CertificationAssessment
  productId: number
  publicId: string
  published: boolean
  onRetry: () => void
}) {
  const queryClient = useQueryClient()
  const verdict = VERDICT_STYLE[assessment.verdict] ?? VERDICT_STYLE.NOT_READY

  const publish = useMutation({
    mutationFn: (next: boolean) =>
      api.publishCertification(productId, assessment.standard, next),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['product', productId] })
      queryClient.invalidateQueries({ queryKey: ['passport', publicId] })
    },
  })

  return (
    <div className="stack stack-5">
      <section className="card card-pad">
        <div className="row row-between row-wrap" style={{ alignItems: 'flex-start' }}>
          <div>
            <span className={`badge ${verdict.cls}`}>
              {verdict.icon} {CERT_VERDICT_LABELS[assessment.verdict]}
            </span>
            <div className="kpi-value" style={{ marginTop: 'var(--sp-3)' }}>
              {assessment.overall_score}
              <span className="kpi-unit">% de cumplimiento</span>
            </div>
          </div>
          <button type="button" className="btn btn-secondary" onClick={onRetry}>
            Repetir diagnóstico
          </button>
        </div>

        <div
          className="row row-between row-wrap"
          style={{
            marginTop: 'var(--sp-5)',
            paddingTop: 'var(--sp-4)',
            borderTop: '1px dashed var(--line)',
          }}
        >
          <div style={{ maxWidth: '48ch' }}>
            <p className="small" style={{ fontWeight: 600 }}>
              {published ? '✓ Publicado en el pasaporte público' : 'Publicar en el pasaporte'}
            </p>
            <p className="small muted">
              Solo se muestra el veredicto y el puntaje ({assessment.overall_score}%). Las
              brechas y la hoja de ruta siguen siendo privadas.
            </p>
          </div>
          <label className="row" style={{ gap: 'var(--sp-2)', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={published}
              onChange={(e) => publish.mutate(e.target.checked)}
              disabled={publish.isPending}
            />
            <span className="small">Visible públicamente</span>
          </label>
        </div>
        {publish.error != null && (
          <div style={{ marginTop: 'var(--sp-3)' }}>
            <ErrorNote error={publish.error} />
          </div>
        )}

        {assessment.critical_gaps.length > 0 && (
          <div style={{ marginTop: 'var(--sp-5)' }}>
            <span className="eyebrow">
              Requisitos críticos sin cumplir ({assessment.critical_gaps.length})
            </span>
            {assessment.critical_gaps.map((gap) => (
              <div className="insight" key={gap.id}>
                <span className="badge badge-danger">✕</span>
                <p className="insight-detail" style={{ marginTop: 0 }}>
                  {gap.text}
                </p>
              </div>
            ))}
          </div>
        )}
      </section>

      <section className="card card-pad">
        <h2 className="chart-title" style={{ marginBottom: 'var(--sp-4)' }}>
          Puntaje por sección
        </h2>
        <div className="bar-rows">
          {assessment.section_scores.map((section) => (
            <div className="bar-row" key={section.id}>
              <span className="bar-row-label">{section.name}</span>
              <span className="bar-row-value">{section.score}%</span>
              <div
                className="bar-track"
                role="img"
                aria-label={`${section.name}: ${section.score}%`}
              >
                <div className="bar-fill" style={{ width: `${section.score}%` }} />
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="card card-pad stack stack-4">
        <div className="row row-between row-wrap">
          <h2 className="chart-title">Hoja de ruta</h2>
          <AiBadge generated={assessment.generated_by_ai} />
        </div>

        {assessment.roadmap_summary && <p className="lede">{assessment.roadmap_summary}</p>}

        {assessment.roadmap_steps.length === 0 ? (
          <p className="muted small">Sin pasos disponibles.</p>
        ) : (
          <div>
            {assessment.roadmap_steps.map((step, index) => {
              const badge = priorityBadge(step.priority)
              return (
                <div className="insight" key={index}>
                  <span className={`badge ${badge.cls}`}>{badge.label}</span>
                  <div>
                    <div className="insight-title">{step.title}</div>
                    <p className="insight-detail">{step.detail}</p>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </section>
    </div>
  )
}
