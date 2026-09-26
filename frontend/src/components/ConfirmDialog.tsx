/** Diálogo de confirmación para acciones destructivas (eliminar finca, eliminar lote…).
 *
 * El foco por defecto va en "Cancelar", no en la acción peligrosa: así una tecla
 * Enter accidental nunca borra algo. Cierra con Escape o clic fuera del panel.
 */

import { useEffect, useRef, type ReactNode } from 'react'

export default function ConfirmDialog({
  open,
  title,
  body,
  confirmLabel = 'Eliminar',
  cancelLabel = 'Cancelar',
  busy = false,
  error,
  onConfirm,
  onCancel,
}: {
  open: boolean
  title: string
  body: ReactNode
  confirmLabel?: string
  cancelLabel?: string
  busy?: boolean
  error?: unknown
  onConfirm: () => void
  onCancel: () => void
}) {
  const cancelRef = useRef<HTMLButtonElement>(null)

  useEffect(() => {
    if (!open) return
    cancelRef.current?.focus()

    function handleKey(event: KeyboardEvent) {
      if (event.key === 'Escape') onCancel()
    }
    document.addEventListener('keydown', handleKey)
    return () => document.removeEventListener('keydown', handleKey)
  }, [open, onCancel])

  if (!open) return null

  return (
    <div className="modal-scrim" onClick={onCancel}>
      <div
        className="modal-card"
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="confirm-dialog-title"
        onClick={(event) => event.stopPropagation()}
      >
        <h2 id="confirm-dialog-title" className="display display-sm">
          {title}
        </h2>
        <div className="small muted" style={{ marginTop: 'var(--sp-2)', lineHeight: 1.6 }}>
          {body}
        </div>

        {error != null && (
          <div className="form-error" style={{ marginTop: 'var(--sp-4)' }} role="alert">
            <span aria-hidden="true">⚠</span>
            <span>
              {error instanceof Error ? error.message : 'No se pudo completar la acción.'}
            </span>
          </div>
        )}

        <div
          className="row"
          style={{ gap: 'var(--sp-3)', marginTop: 'var(--sp-5)', justifyContent: 'flex-end' }}
        >
          <button
            ref={cancelRef}
            type="button"
            className="btn btn-ghost"
            onClick={onCancel}
            disabled={busy}
          >
            {cancelLabel}
          </button>
          <button
            type="button"
            className="btn btn-danger-solid"
            onClick={onConfirm}
            disabled={busy}
          >
            {busy ? <span className="spin" /> : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  )
}
