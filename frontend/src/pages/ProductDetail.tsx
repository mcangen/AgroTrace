import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { api, downloadProductReport, passportQrSrc } from '../lib/api'
import AiPanel from '../components/AiPanel'
import ChainTimeline from '../components/ChainTimeline'
import ConfirmDialog from '../components/ConfirmDialog'
import EventForm from '../components/EventForm'
import { ChainBadge, ErrorNote, Spinner, StatusBadge } from '../components/ui'
import { formatDate, formatNumber } from '../lib/format'

export default function ProductDetail() {
  const { id } = useParams<{ id: string }>()
  const productId = Number(id)
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const [showForm, setShowForm] = useState(false)
  const [confirmDelete, setConfirmDelete] = useState(false)
  const [downloading, setDownloading] = useState(false)
  const [downloadError, setDownloadError] = useState<unknown>(null)

  const product = useQuery({
    queryKey: ['product', productId],
    queryFn: () => api.getProduct(productId),
    enabled: Number.isFinite(productId),
  })
  const events = useQuery({
    queryKey: ['events', productId],
    queryFn: () => api.listEvents(productId),
    enabled: Number.isFinite(productId),
  })
  const verification = useQuery({
    queryKey: ['verify', productId],
    queryFn: () => api.verifyChain(productId),
    enabled: Number.isFinite(productId),
  })

  const remove = useMutation({
    mutationFn: () => api.deleteProduct(productId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['products'] })
      queryClient.invalidateQueries({ queryKey: ['farms'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      navigate('/panel/lotes', { replace: true })
    },
  })

  const toggleDirectory = useMutation({
    mutationFn: (directoryListed: boolean) =>
      api.updateProduct(productId, { directory_listed: directoryListed }),
    onSuccess: (updated) => {
      queryClient.setQueryData(['product', productId], updated)
      queryClient.invalidateQueries({ queryKey: ['directory'] })
    },
  })

  if (!Number.isFinite(productId)) return <ErrorNote error={new Error('Lote inválido.')} />
  if (product.isLoading) return <Spinner label="Cargando lote…" />
  if (product.error) return <ErrorNote error={product.error} />
  if (!product.data) return null

  const item = product.data

  async function downloadReport() {
    setDownloadError(null)
    setDownloading(true)
    try {
      await downloadProductReport(productId, `trazabilidad-${item.public_id}.pdf`)
    } catch (error) {
      setDownloadError(error)
    } finally {
      setDownloading(false)
    }
  }

  return (
    <div className="stack stack-6">
      <header>
        <Link to="/panel/lotes" className="small muted">
          ← Lotes
        </Link>
        <div
          className="page-head"
          style={{ marginTop: 'var(--sp-2)', marginBottom: 'var(--sp-3)' }}
        >
          <div>
            <div className="row row-wrap" style={{ gap: 'var(--sp-2)' }}>
              <StatusBadge status={item.status} />
              {verification.data && <ChainBadge verification={verification.data} />}
            </div>
            <h1 className="display display-lg" style={{ marginTop: 'var(--sp-3)' }}>
              {item.name}
            </h1>
            <p className="lede" style={{ marginTop: 'var(--sp-2)' }}>
              {item.variety ? `${item.variety} · ` : ''}
              {item.farm_name} · {item.farm_location}
            </p>
          </div>
          <div className="product-actions">
            <a
              href={`/p/${item.public_id}`}
              target="_blank"
              rel="noreferrer"
              className="btn btn-secondary"
            >
              Ver pasaporte público ↗
            </a>
            <Link to={`/panel/lotes/${productId}/certificaciones`} className="btn btn-secondary">
              🏅 Certificación
            </Link>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={downloadReport}
              disabled={downloading}
            >
              {downloading ? <span className="spin" /> : '📄 Reporte PDF'}
            </button>
            <button className="btn btn-primary" onClick={() => setShowForm((v) => !v)}>
              {showForm ? 'Cerrar' : '+ Sellar evento'}
            </button>
            <button
              type="button"
              className="btn btn-danger"
              onClick={() => setConfirmDelete(true)}
            >
              🗑 Eliminar
            </button>
          </div>
        </div>
      </header>

      {verification.data && !verification.data.valid && (
        <div className="form-error" role="alert">
          <span aria-hidden="true">⚠</span>
          <span>{verification.data.message}</span>
        </div>
      )}

      {downloadError != null && <ErrorNote error={downloadError} />}

      {showForm && (
        <EventForm productId={productId} onDone={() => setShowForm(false)} />
      )}

      <section className="kpi-grid">
        <div className="kpi">
          <span className="kpi-label">Eventos sellados</span>
          <span className="kpi-value">{formatNumber(item.event_count)}</span>
        </div>
        <div className="kpi">
          <span className="kpi-label">Reputación</span>
          <span className="kpi-value">
            {item.reputation_score.toFixed(1)}
            <span className="kpi-unit">/5</span>
          </span>
        </div>
        <div className="kpi">
          <span className="kpi-label">Siembra</span>
          <span className="kpi-value" style={{ fontSize: '1.25rem' }}>
            {formatDate(item.planting_date)}
          </span>
        </div>
        <div className="kpi">
          <span className="kpi-label">Cosecha</span>
          <span className="kpi-value" style={{ fontSize: '1.25rem' }}>
            {formatDate(item.harvest_date)}
          </span>
        </div>
      </section>

      <div className="chart-grid">
        <section className="card card-pad">
          <div className="card-head">
            <div>
              <h2 className="display display-sm">Cadena de trazabilidad</h2>
              <p className="small muted" style={{ marginTop: 2 }}>
                {verification.data?.message ?? 'Verificando…'}
              </p>
            </div>
          </div>

          {events.isLoading ? (
            <Spinner />
          ) : events.error ? (
            <ErrorNote error={events.error} />
          ) : (
            <ChainTimeline
              events={events.data ?? []}
              verification={verification.data}
            />
          )}
        </section>

        <div className="stack stack-4">
          <section className="card card-pad stack stack-4">
            <h2 className="display display-sm">Pasaporte público</h2>
            <div className="qr-box">
              <img
                src={passportQrSrc(item.public_id)}
                alt={`Código QR del pasaporte de ${item.name}`}
                width={108}
                height={108}
              />
              <div className="stack stack-2" style={{ minWidth: 0 }}>
                <span className="small muted">Identificador público</span>
                <code className="hash">{item.public_id}</code>
                <a
                  href={passportQrSrc(item.public_id)}
                  download={`qr-${item.public_id}.png`}
                  className="btn btn-secondary btn-sm"
                >
                  Descargar QR
                </a>
              </div>
            </div>

            <label className="row row-between" style={{ cursor: 'pointer' }}>
              <span className="small">
                Listar en el{' '}
                <a href="/directorio" target="_blank" rel="noreferrer">
                  directorio público
                </a>
              </span>
              <input
                type="checkbox"
                checked={item.directory_listed}
                onChange={(e) => toggleDirectory.mutate(e.target.checked)}
                disabled={toggleDirectory.isPending}
              />
            </label>
            {toggleDirectory.error != null && <ErrorNote error={toggleDirectory.error} />}
          </section>

          {item.insumos && (
            <section className="card card-pad stack stack-2">
              <span className="eyebrow">Insumos</span>
              <p className="small">{item.insumos}</p>
            </section>
          )}

          {item.post_cosecha && (
            <section className="card card-pad stack stack-2">
              <span className="eyebrow">Post-cosecha</span>
              <p className="small">{item.post_cosecha}</p>
            </section>
          )}
        </div>
      </div>

      <AiPanel productId={productId} />

      <ConfirmDialog
        open={confirmDelete}
        title={`¿Eliminar ${item.name}?`}
        body={
          item.event_count > 0 ? (
            <>
              Este lote tiene <strong>{formatNumber(item.event_count)}</strong>{' '}
              {item.event_count === 1
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
          setConfirmDelete(false)
          remove.reset()
        }}
        onConfirm={() => remove.mutate()}
      />
    </div>
  )
}
