/** Bandeja de mensajes que los compradores envían desde el pasaporte público. */

import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { api } from '../lib/api'
import ConfirmDialog from '../components/ConfirmDialog'
import { EmptyState, ErrorNote, Spinner } from '../components/ui'
import { formatDateTime, formatRelative } from '../lib/format'
import type { Inquiry } from '../lib/types'

export default function Inquiries() {
  const queryClient = useQueryClient()
  const [unreadOnly, setUnreadOnly] = useState(false)
  const [toDelete, setToDelete] = useState<Inquiry | null>(null)

  const inquiries = useQuery({
    queryKey: ['inquiries', unreadOnly],
    queryFn: () => api.listInquiries(unreadOnly),
  })

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['inquiries'] })
    queryClient.invalidateQueries({ queryKey: ['inquiries-unread'] })
  }

  const markRead = useMutation({
    mutationFn: (id: number) => api.markInquiryRead(id),
    onSuccess: invalidate,
  })

  const remove = useMutation({
    mutationFn: (id: number) => api.deleteInquiry(id),
    onSuccess: () => {
      invalidate()
      setToDelete(null)
    },
  })

  if (inquiries.isLoading) return <Spinner label="Cargando mensajes…" />
  if (inquiries.error) return <ErrorNote error={inquiries.error} />

  const items = inquiries.data ?? []

  return (
    <div className="stack stack-5" style={{ maxWidth: 820 }}>
      <header className="page-head">
        <div>
          <span className="eyebrow">Compradores</span>
          <h1 className="display display-lg" style={{ marginTop: 'var(--sp-2)' }}>
            Mensajes
          </h1>
          <p className="lede" style={{ marginTop: 'var(--sp-2)' }}>
            Quien escanea el QR de un lote puede escribirte desde su pasaporte público.
          </p>
        </div>
        <label className="row small" style={{ gap: 'var(--sp-2)' }}>
          <input
            type="checkbox"
            checked={unreadOnly}
            onChange={(e) => setUnreadOnly(e.target.checked)}
          />
          Solo sin leer
        </label>
      </header>

      {items.length === 0 ? (
        <EmptyState
          icon="📬"
          title={unreadOnly ? 'No hay mensajes sin leer' : 'Aún no tienes mensajes'}
          body="Cuando un comprador escriba desde el pasaporte público de alguno de tus lotes, el mensaje aparecerá aquí."
        />
      ) : (
        <div className="stack stack-3">
          {items.map((inquiry) => (
            <article
              className={`card card-pad stack stack-3${inquiry.read_at ? '' : ' inquiry-unread'}`}
              key={inquiry.id}
            >
              <div className="row row-between row-wrap" style={{ alignItems: 'flex-start' }}>
                <div>
                  <div className="row row-wrap" style={{ gap: 'var(--sp-2)' }}>
                    <h2 className="product-card-name" style={{ fontSize: '1.05rem' }}>
                      {inquiry.buyer_name}
                    </h2>
                    {!inquiry.read_at && <span className="badge badge-info">Nuevo</span>}
                  </div>
                  <p className="small muted" style={{ marginTop: 2 }}>
                    {inquiry.buyer_country ? `${inquiry.buyer_country} · ` : ''}
                    Interesado en <strong>{inquiry.product_name}</strong>
                  </p>
                </div>
                <span className="small faint" title={formatDateTime(inquiry.created_at)}>
                  {formatRelative(inquiry.created_at)}
                </span>
              </div>

              <p style={{ whiteSpace: 'pre-wrap' }}>{inquiry.message}</p>

              <div className="row row-wrap" style={{ gap: 'var(--sp-3)' }}>
                <a
                  className="btn btn-primary btn-sm"
                  href={`mailto:${inquiry.buyer_email}?subject=${encodeURIComponent(
                    `Sobre ${inquiry.product_name} — AgroTrace`,
                  )}`}
                >
                  ✉ Responder
                </a>
                {!inquiry.read_at && (
                  <button
                    className="btn btn-secondary btn-sm"
                    onClick={() => markRead.mutate(inquiry.id)}
                    disabled={markRead.isPending}
                  >
                    Marcar como leído
                  </button>
                )}
                <button
                  className="btn btn-ghost btn-sm"
                  onClick={() => setToDelete(inquiry)}
                  style={{ marginLeft: 'auto' }}
                >
                  🗑
                </button>
              </div>

              <code className="hash">{inquiry.buyer_email}</code>
            </article>
          ))}
        </div>
      )}

      <ConfirmDialog
        open={toDelete != null}
        title="¿Eliminar este mensaje?"
        body={
          toDelete ? (
            <>
              Se borrará el mensaje de <strong>{toDelete.buyer_name}</strong>. Esta acción no
              se puede deshacer.
            </>
          ) : (
            ''
          )
        }
        busy={remove.isPending}
        error={remove.error}
        onCancel={() => {
          setToDelete(null)
          remove.reset()
        }}
        onConfirm={() => toDelete && remove.mutate(toDelete.id)}
      />
    </div>
  )
}
