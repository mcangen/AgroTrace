/** Piezas pequeñas de interfaz reutilizadas por varias páginas. */

import type { ReactNode } from 'react'
import type { ProductStatus, Verification } from '../lib/types'
import { STATUS_LABELS, STATUS_TONE } from '../lib/format'

export function Spinner({ label }: { label?: string }) {
  return (
    <div className="row" style={{ gap: 'var(--sp-3)', padding: 'var(--sp-5) 0' }}>
      <span className="spin" style={{ color: 'var(--green-600)' }} />
      <span className="muted small">{label ?? 'Cargando…'}</span>
    </div>
  )
}

export function ErrorNote({ error }: { error: unknown }) {
  const message = error instanceof Error ? error.message : 'Ocurrió un error inesperado.'
  return (
    <div className="form-error" role="alert">
      <span aria-hidden="true">⚠</span>
      <span>{message}</span>
    </div>
  )
}

export function EmptyState({
  icon,
  title,
  body,
  action,
}: {
  icon: string
  title: string
  body: string
  action?: ReactNode
}) {
  return (
    <div className="card empty">
      <span className="empty-icon" aria-hidden="true">
        {icon}
      </span>
      <h3 className="display display-sm">{title}</h3>
      <p className="muted small" style={{ maxWidth: '42ch' }}>
        {body}
      </p>
      {action}
    </div>
  )
}

export function StatusBadge({ status }: { status: ProductStatus }) {
  return <span className={`badge ${STATUS_TONE[status]}`}>{STATUS_LABELS[status]}</span>
}

/** La integridad nunca se comunica solo por color: siempre lleva icono y texto. */
export function ChainBadge({ verification }: { verification: Verification }) {
  if (verification.total_events === 0) {
    return <span className="badge badge-neutral">◌ Sin eventos</span>
  }
  return verification.valid ? (
    <span className="badge badge-ok">✓ Cadena íntegra</span>
  ) : (
    <span className="badge badge-danger">✕ Cadena alterada</span>
  )
}

export function AiBadge({ generated }: { generated: boolean }) {
  return generated ? (
    <span className="badge badge-ai">✦ Generado por Gemini</span>
  ) : (
    <span className="badge badge-warn">◌ Contenido de respaldo</span>
  )
}

export function Field({
  label,
  hint,
  children,
}: {
  label: string
  hint?: string
  children: ReactNode
}) {
  return (
    <label className="field">
      <span className="field-label">{label}</span>
      {children}
      {hint && <span className="field-hint">{hint}</span>}
    </label>
  )
}
