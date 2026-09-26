/** Directorio público de productores: descubrir lotes sin necesitar un QR.
 *
 * Página pública, sin sesión — mismo espíritu que el pasaporte público. Solo
 * lista lotes que su dueño marcó explícitamente como visibles.
 */

import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'

import { api } from '../lib/api'
import Brand from '../components/Brand'
import { EmptyState, ErrorNote, Spinner } from '../components/ui'
import { STATUS_LABELS } from '../lib/format'

export default function Directory() {
  const [query, setQuery] = useState('')

  const { data, isLoading, error } = useQuery({
    queryKey: ['directory'],
    queryFn: api.directory,
  })

  const filtered = useMemo(() => {
    if (!data) return []
    const needle = query.trim().toLowerCase()
    if (!needle) return data
    return data.filter(
      (entry) =>
        entry.product_name.toLowerCase().includes(needle) ||
        entry.farm_name.toLowerCase().includes(needle) ||
        entry.location.toLowerCase().includes(needle) ||
        (entry.variety ?? '').toLowerCase().includes(needle),
    )
  }, [data, query])

  return (
    <div className="passport-page">
      <header className="passport-hero">
        <div className="passport-wrap stack stack-4">
          <div className="row row-between row-wrap">
            <Brand onDark />
            <Link to="/" className="small" style={{ color: 'var(--ink-on-dark-muted)' }}>
              ← AgroTrace
            </Link>
          </div>
          <div>
            <span className="eyebrow eyebrow-light">Directorio público</span>
            <h1 className="passport-title" style={{ marginTop: 'var(--sp-3)' }}>
              Productores verificados
            </h1>
            <p
              className="lede"
              style={{ color: 'var(--ink-on-dark-muted)', marginTop: 'var(--sp-2)' }}
            >
              Lotes con trazabilidad verificable, listados por sus propios productores.
            </p>
          </div>
        </div>
      </header>

      <main className="passport-body stack stack-5">
        <section className="card card-pad">
          <input
            className="input"
            placeholder="Buscar por producto, finca, variedad o ubicación…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            aria-label="Buscar en el directorio"
          />
        </section>

        {isLoading ? (
          <Spinner label="Cargando directorio…" />
        ) : error ? (
          <ErrorNote error={error} />
        ) : !data || data.length === 0 ? (
          <EmptyState
            icon="🌎"
            title="Aún no hay lotes públicos"
            body="Los productores deciden, lote por lote, si aparecen aquí. Vuelve pronto."
          />
        ) : filtered.length === 0 ? (
          <EmptyState icon="🔍" title="Nada coincide" body="Prueba con otro término de búsqueda." />
        ) : (
          <div className="product-grid">
            {filtered.map((entry) => (
              <Link to={`/p/${entry.public_id}`} className="product-card" key={entry.public_id}>
                {entry.thumbnail_url ? (
                  <img
                    src={entry.thumbnail_url}
                    alt=""
                    style={{
                      width: '100%',
                      aspectRatio: '16/9',
                      objectFit: 'cover',
                      borderRadius: 'var(--r-md)',
                    }}
                  />
                ) : (
                  <div
                    style={{
                      width: '100%',
                      aspectRatio: '16/9',
                      borderRadius: 'var(--r-md)',
                      background: 'var(--surface-sunk)',
                      display: 'grid',
                      placeItems: 'center',
                      fontSize: '1.75rem',
                    }}
                    aria-hidden="true"
                  >
                    🌱
                  </div>
                )}

                <div>
                  <h2 className="product-card-name">{entry.product_name}</h2>
                  <p className="small muted" style={{ marginTop: 2 }}>
                    {entry.variety ? `${entry.variety} · ` : ''}
                    {entry.farm_name}
                  </p>
                </div>

                <p className="small faint">{entry.location}</p>

                <div className="product-card-stats">
                  <div>
                    <div className="product-stat-value">
                      {entry.reputation_score.toFixed(1)}
                    </div>
                    <div className="product-stat-label">reputación</div>
                  </div>
                  <div>
                    <div className="product-stat-value">{STATUS_LABELS[entry.status]}</div>
                    <div className="product-stat-label">estado</div>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </main>
    </div>
  )
}
