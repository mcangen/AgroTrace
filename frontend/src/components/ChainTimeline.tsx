/** La cadena de trazabilidad como línea de tiempo verificable.
 *
 * Cuando la verificación señala un eslabón roto, ese evento y todos los que le
 * siguen se marcan: es exactamente lo que ocurre con un hash encadenado, y
 * mostrarlo así explica el mecanismo mejor que un mensaje de error.
 */

import type { TraceEvent, Verification } from '../lib/types'
import {
  EVENT_ICONS,
  EVENT_LABELS,
  formatDateTime,
  humanizeKey,
  shortHash,
} from '../lib/format'

export default function ChainTimeline({
  events,
  verification,
}: {
  events: TraceEvent[]
  verification?: Verification
}) {
  if (events.length === 0) {
    return (
      <p className="muted small">
        Este lote todavía no tiene eventos. Registra el primero para abrir la cadena.
      </p>
    )
  }

  const breakAt = verification?.valid === false ? verification.broken_at_sequence : null

  return (
    <div className="chain">
      {events.map((event) => {
        const isBroken = breakAt !== null && event.sequence === breakAt
        const isAfterBreak = breakAt !== null && event.sequence > breakAt
        // `fotos_sha256` se sella en el payload, pero en pantalla se muestran
        // las fotos mismas, no la lista de huellas.
        const payloadEntries = Object.entries(event.payload).filter(
          ([key, value]) =>
            key !== 'fotos_sha256' && value !== null && value !== '' && value !== undefined,
        )

        return (
          <article
            key={event.id}
            className={`chain-item${isBroken ? ' broken' : ''}${
              isAfterBreak ? ' after-break' : ''
            }`}
          >
            <div className="chain-dot" aria-hidden="true">
              {EVENT_ICONS[event.event_type] ?? '◆'}
            </div>

            <div className="chain-body">
              <div className="row row-between row-wrap" style={{ gap: 'var(--sp-2)' }}>
                <div>
                  <h3 className="chain-title">
                    {EVENT_LABELS[event.event_type] ?? event.event_type}
                  </h3>
                  <p className="small muted">
                    {formatDateTime(event.occurred_at)}
                    {event.recorded_by && ` · ${event.recorded_by}`}
                  </p>
                </div>
                <div className="row" style={{ gap: 'var(--sp-2)' }}>
                  <span className="badge badge-neutral mono">#{event.sequence}</span>
                  {isBroken && <span className="badge badge-danger">✕ Alterado</span>}
                  {isAfterBreak && (
                    <span className="badge badge-warn">◌ Cadena rota antes</span>
                  )}
                </div>
              </div>

              {event.note && (
                <p className="small" style={{ marginTop: 'var(--sp-2)' }}>
                  {event.note}
                </p>
              )}

              {payloadEntries.length > 0 && (
                <div className="payload-grid">
                  {payloadEntries.map(([key, value]) => (
                    <div key={key}>
                      <div className="payload-key">{humanizeKey(key)}</div>
                      <div className="payload-value">{String(value)}</div>
                    </div>
                  ))}
                </div>
              )}

              {event.photos.length > 0 && (
                <div style={{ marginTop: 'var(--sp-3)' }}>
                  <div className="payload-key" style={{ marginBottom: 'var(--sp-2)' }}>
                    Evidencia fotográfica ({event.photos.length})
                  </div>
                  <div className="photo-grid">
                    {event.photos.map((photo) => (
                      <figure
                        className={`photo-thumb${photo.integrity_ok ? '' : ' tampered'}`}
                        key={photo.id}
                      >
                        <a href={photo.url} target="_blank" rel="noreferrer">
                          <img
                            src={photo.url}
                            alt={photo.caption ?? photo.filename}
                            loading="lazy"
                          />
                        </a>
                        {!photo.integrity_ok && (
                          <span className="photo-badge" title="El archivo no coincide con la huella sellada">
                            ✕ alterada
                          </span>
                        )}
                        {photo.caption && <figcaption>{photo.caption}</figcaption>}
                      </figure>
                    ))}
                  </div>
                </div>
              )}

              <div className="chain-hashes">
                <span className="small faint">anterior</span>
                <code className="hash" title={event.prev_hash}>
                  {shortHash(event.prev_hash)}
                </code>
                <span className="small faint" aria-hidden="true">
                  →
                </span>
                <span className="small faint">sello</span>
                <code className="hash" title={event.chain_hash}>
                  {shortHash(event.chain_hash)}
                </code>
              </div>
            </div>
          </article>
        )
      })}
    </div>
  )
}
