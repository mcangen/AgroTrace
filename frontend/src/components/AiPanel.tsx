/** Panel de agentes de IA de un lote.
 *
 * Cada agente es una acción explícita del usuario, no algo que corre solo: el
 * productor ve qué se generó, con qué modelo y si vino del modelo o del respaldo.
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { api } from '../lib/api'
import { AiBadge, ErrorNote } from './ui'
import type { ExportSheetResult, InsightsResult, StoryResult } from '../lib/types'

function SeverityBadge({ severity }: { severity: string }) {
  const normalized = severity.toLowerCase()
  if (normalized.includes('riesgo')) return <span className="badge badge-danger">⚠ Riesgo</span>
  if (normalized.includes('oportun'))
    return <span className="badge badge-ok">↗ Oportunidad</span>
  return <span className="badge badge-info">ℹ Info</span>
}

export default function AiPanel({ productId }: { productId: number }) {
  const queryClient = useQueryClient()

  const { data: aiStatus } = useQuery({
    queryKey: ['ai-status'],
    queryFn: api.aiStatus,
    staleTime: 5 * 60_000,
  })

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['passport', productId] })
    queryClient.invalidateQueries({ queryKey: ['dashboard'] })
    queryClient.invalidateQueries({ queryKey: ['products'] })
  }

  const story = useMutation<StoryResult>({
    mutationFn: () => api.generateStory(productId),
    onSuccess: invalidate,
  })
  const sheet = useMutation<ExportSheetResult>({
    mutationFn: () => api.generateExportSheet(productId),
    onSuccess: invalidate,
  })
  const insights = useMutation<InsightsResult>({
    mutationFn: () => api.generateInsights(productId),
    onSuccess: invalidate,
  })

  const busy = story.isPending || sheet.isPending || insights.isPending

  return (
    <section className="ai-panel stack stack-4">
      <div className="card-head" style={{ marginBottom: 0 }}>
        <div>
          <h2 className="display display-sm">Agentes de IA</h2>
          <p className="small muted" style={{ marginTop: 2 }}>
            Trabajan solo con los datos sellados en la cadena de este lote.
          </p>
        </div>
        {aiStatus && (
          <span className={`badge ${aiStatus.enabled ? 'badge-ai' : 'badge-warn'}`}>
            {aiStatus.enabled ? `✦ ${aiStatus.model}` : '◌ Sin API key'}
          </span>
        )}
      </div>

      {aiStatus && !aiStatus.enabled && (
        <p className="small" style={{ color: 'var(--amber-ink)' }}>
          {aiStatus.reason} Los agentes seguirán respondiendo, pero con contenido de
          respaldo genérico.
        </p>
      )}

      <div className="ai-actions">
        <button
          className="btn btn-secondary"
          onClick={() => story.mutate()}
          disabled={busy}
        >
          {story.isPending ? <span className="spin" /> : '✍️ Narrativa'}
        </button>
        <button
          className="btn btn-secondary"
          onClick={() => sheet.mutate()}
          disabled={busy}
        >
          {sheet.isPending ? <span className="spin" /> : '📋 Ficha de exportación'}
        </button>
        <button
          className="btn btn-secondary"
          onClick={() => insights.mutate()}
          disabled={busy}
        >
          {insights.isPending ? <span className="spin" /> : '🔬 Análisis agronómico'}
        </button>
      </div>

      {story.error != null && <ErrorNote error={story.error} />}
      {sheet.error != null && <ErrorNote error={sheet.error} />}
      {insights.error != null && <ErrorNote error={insights.error} />}

      {story.data && (
        <div className="ai-output stack stack-3">
          <div className="row row-between">
            <h3 className="eyebrow">Historia de origen</h3>
            <AiBadge generated={story.data.generated_by_ai} />
          </div>
          <p className="ai-story">{story.data.story_es}</p>
          <details>
            <summary className="small muted" style={{ cursor: 'pointer' }}>
              Ver versión en inglés
            </summary>
            <p className="ai-story" style={{ marginTop: 'var(--sp-3)' }}>
              {story.data.story_en}
            </p>
          </details>
          {story.data.tasting_notes && (
            <p className="small muted">
              <strong>Notas:</strong> {story.data.tasting_notes}
            </p>
          )}
        </div>
      )}

      {sheet.data && (
        <div className="ai-output stack stack-3">
          <div className="row row-between">
            <h3 className="eyebrow">Ficha de exportación</h3>
            <AiBadge generated={sheet.data.generated_by_ai} />
          </div>
          <div>
            <h4 className="display display-sm">{sheet.data.title_es}</h4>
            <p style={{ marginTop: 'var(--sp-2)' }}>{sheet.data.body_es}</p>
          </div>
          <div style={{ paddingTop: 'var(--sp-3)', borderTop: '1px dashed var(--line)' }}>
            <h4 className="display display-sm">{sheet.data.title_en}</h4>
            <p style={{ marginTop: 'var(--sp-2)' }}>{sheet.data.body_en}</p>
          </div>
        </div>
      )}

      {insights.data && (
        <div className="ai-output stack stack-3">
          <div className="row row-between">
            <h3 className="eyebrow">Análisis agronómico</h3>
            <AiBadge generated={insights.data.generated_by_ai} />
          </div>
          <p>{insights.data.summary}</p>
          <p className="small muted">
            Calidad de trazabilidad estimada:{' '}
            <strong>{insights.data.quality_score.toFixed(1)} / 5</strong>
          </p>
          <div>
            {insights.data.items.map((item, index) => (
              <div className="insight" key={`${item.title}-${index}`}>
                <SeverityBadge severity={item.severity} />
                <div>
                  <div className="insight-title">{item.title}</div>
                  <p className="insight-detail">{item.detail}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </section>
  )
}
