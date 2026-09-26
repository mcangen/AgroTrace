import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { api } from '../lib/api'
import ConfirmDialog from '../components/ConfirmDialog'
import { EmptyState, ErrorNote, Spinner, StatusBadge } from '../components/ui'
import { formatDate, formatNumber, STATUS_LABELS } from '../lib/format'
import type { Product, ProductStatus } from '../lib/types'

const STATUSES = Object.keys(STATUS_LABELS) as ProductStatus[]

export default function Products() {
  const queryClient = useQueryClient()
  const [query, setQuery] = useState('')
  const [status, setStatus] = useState<ProductStatus | 'ALL'>('ALL')
  const [productToDelete, setProductToDelete] = useState<Product | null>(null)

  const { data, isLoading, error } = useQuery({
    queryKey: ['products'],
    queryFn: () => api.listProducts(),
  })

  // Eliminar un lote elimina en cascada sus eventos sellados y su pasaporte.
  const remove = useMutation({
    mutationFn: (id: number) => api.deleteProduct(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['products'] })
      queryClient.invalidateQueries({ queryKey: ['farms'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      setProductToDelete(null)
    },
  })

  const filtered = useMemo(() => {
    if (!data) return []
    const needle = query.trim().toLowerCase()
    return data.filter((product) => {
      if (status !== 'ALL' && product.status !== status) return false
      if (!needle) return true
      return (
        product.name.toLowerCase().includes(needle) ||
        product.farm_name.toLowerCase().includes(needle) ||
        (product.variety ?? '').toLowerCase().includes(needle)
      )
    })
  }, [data, query, status])

  if (isLoading) return <Spinner label="Cargando lotes…" />
  if (error) return <ErrorNote error={error} />

  return (
    <div className="stack stack-5">
      <header className="page-head">
        <div>
          <span className="eyebrow">Trazabilidad</span>
          <h1 className="display display-lg" style={{ marginTop: 'var(--sp-2)' }}>
            Lotes
          </h1>
        </div>
        <Link to="/panel/lotes/nuevo" className="btn btn-primary">
          + Registrar lote
        </Link>
      </header>

      {data && data.length > 0 && (
        <div className="row row-wrap" style={{ gap: 'var(--sp-3)' }}>
          <input
            className="input"
            style={{ maxWidth: 280 }}
            placeholder="Buscar por lote, finca o variedad…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            aria-label="Buscar lotes"
          />
          <select
            className="select"
            style={{ maxWidth: 180 }}
            value={status}
            onChange={(e) => setStatus(e.target.value as ProductStatus | 'ALL')}
            aria-label="Filtrar por estado"
          >
            <option value="ALL">Todos los estados</option>
            {STATUSES.map((value) => (
              <option key={value} value={value}>
                {STATUS_LABELS[value]}
              </option>
            ))}
          </select>
          <span className="muted small">
            {formatNumber(filtered.length)} de {formatNumber(data.length)}
          </span>
        </div>
      )}

      {!data || data.length === 0 ? (
        <EmptyState
          icon="❏"
          title="Todavía no hay lotes"
          body="Un lote es una cosecha o partida que quieres poder trazar de principio a fin."
          action={
            <Link to="/panel/lotes/nuevo" className="btn btn-primary">
              Registrar lote
            </Link>
          }
        />
      ) : filtered.length === 0 ? (
        <EmptyState
          icon="🔍"
          title="Ningún lote coincide"
          body="Prueba con otro término de búsqueda o cambia el filtro de estado."
        />
      ) : (
        <div className="product-grid">
          {filtered.map((product) => (
            <article className="product-card" key={product.id}>
              <div className="row row-between" style={{ alignItems: 'flex-start' }}>
                <StatusBadge status={product.status} />
                <div className="row" style={{ gap: 'var(--sp-1)' }}>
                  {product.has_story && <span className="badge badge-ai">✦ Narrativa</span>}
                  <button
                    type="button"
                    className="icon-btn icon-btn-danger"
                    onClick={() => setProductToDelete(product)}
                    aria-label={`Eliminar ${product.name}`}
                    title="Eliminar lote"
                  >
                    🗑
                  </button>
                </div>
              </div>

              <Link to={`/panel/lotes/${product.id}`} className="product-card-link">
                <div>
                  <h2 className="product-card-name">{product.name}</h2>
                  <p className="small muted" style={{ marginTop: 2 }}>
                    {product.variety ? `${product.variety} · ` : ''}
                    {product.farm_name}
                  </p>
                </div>

                <p className="small faint">
                  {product.harvest_date
                    ? `Cosecha: ${formatDate(product.harvest_date)}`
                    : product.planting_date
                      ? `Siembra: ${formatDate(product.planting_date)}`
                      : product.farm_location}
                </p>

                <div className="product-card-stats">
                  <div>
                    <div className="product-stat-value">
                      {formatNumber(product.event_count)}
                    </div>
                    <div className="product-stat-label">eventos</div>
                  </div>
                  <div>
                    <div className="product-stat-value">
                      {product.reputation_score.toFixed(1)}
                    </div>
                    <div className="product-stat-label">reputación</div>
                  </div>
                </div>
              </Link>
            </article>
          ))}
        </div>
      )}

      <ConfirmDialog
        open={productToDelete != null}
        title={`¿Eliminar ${productToDelete?.name ?? 'este lote'}?`}
        body={
          productToDelete && productToDelete.event_count > 0 ? (
            <>
              Este lote tiene <strong>{formatNumber(productToDelete.event_count)}</strong>{' '}
              {productToDelete.event_count === 1
                ? 'evento sellado en su cadena'
                : 'eventos sellados en su cadena'}
              . Al eliminarlo también se eliminarán esos eventos y su pasaporte público
              (el QR dejará de funcionar). Esta acción no se puede deshacer.
            </>
          ) : (
            'Esta acción no se puede deshacer.'
          )
        }
        busy={remove.isPending}
        error={remove.error}
        onCancel={() => {
          setProductToDelete(null)
          remove.reset()
        }}
        onConfirm={() => productToDelete && remove.mutate(productToDelete.id)}
      />
    </div>
  )
}
