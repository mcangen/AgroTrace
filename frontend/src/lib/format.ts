/** Etiquetas en español y formateo para la interfaz. */

import type { AgentKind, CertificationVerdict, EventType, ProductStatus } from './types'

export const EVENT_LABELS: Record<EventType, string> = {
  REGISTRO_INICIAL: 'Registro inicial',
  SIEMBRA: 'Siembra',
  LABOR_CULTURAL: 'Labor cultural',
  FERTILIZACION: 'Fertilización',
  CONTROL_FITOSANITARIO: 'Control fitosanitario',
  COSECHA: 'Cosecha',
  POST_COSECHA: 'Post-cosecha',
  SECADO: 'Secado',
  CONTROL_CALIDAD: 'Control de calidad',
  EMPAQUE: 'Empaque',
  CERTIFICACION: 'Certificación',
  DESPACHO: 'Despacho',
}

export const EVENT_ICONS: Record<EventType, string> = {
  REGISTRO_INICIAL: '◆',
  SIEMBRA: '🌱',
  LABOR_CULTURAL: '🪴',
  FERTILIZACION: '🧺',
  CONTROL_FITOSANITARIO: '🛡',
  COSECHA: '🧑‍🌾',
  POST_COSECHA: '🫙',
  SECADO: '☀️',
  CONTROL_CALIDAD: '🔬',
  EMPAQUE: '📦',
  CERTIFICACION: '🏅',
  DESPACHO: '🚚',
}

export const EVENT_ORDER: EventType[] = [
  'SIEMBRA',
  'LABOR_CULTURAL',
  'FERTILIZACION',
  'CONTROL_FITOSANITARIO',
  'COSECHA',
  'POST_COSECHA',
  'SECADO',
  'CONTROL_CALIDAD',
  'EMPAQUE',
  'CERTIFICACION',
  'DESPACHO',
]

export const STATUS_LABELS: Record<ProductStatus, string> = {
  DRAFT: 'Borrador',
  GROWING: 'En cultivo',
  HARVESTED: 'Cosechado',
  PROCESSING: 'En proceso',
  READY: 'Listo',
  EXPORTED: 'Exportado',
}

export const STATUS_TONE: Record<ProductStatus, string> = {
  DRAFT: 'badge-neutral',
  GROWING: 'badge-info',
  HARVESTED: 'badge-warn',
  PROCESSING: 'badge-warn',
  READY: 'badge-ok',
  EXPORTED: 'badge-ok',
}

export const AGENT_LABELS: Record<AgentKind, string> = {
  STORYTELLING: 'Narrativa',
  EXPORT_SHEET: 'Ficha de exportación',
  INSIGHTS: 'Análisis agronómico',
  ASSISTANT: 'Asistente',
  CERTIFICATION: 'Diagnóstico de certificación',
}

export const CERT_VERDICT_LABELS: Record<CertificationVerdict, string> = {
  READY: 'Listo para auditoría',
  ALMOST_READY: 'Casi listo',
  NOT_READY: 'Preparación requerida',
}

/** Nombra los campos técnicos del payload en la interfaz. */
export function humanizeKey(key: string): string {
  const cleaned = key.replace(/_/g, ' ').trim()
  return cleaned.charAt(0).toUpperCase() + cleaned.slice(1)
}

export function formatDate(iso: string | null | undefined): string {
  if (!iso) return '—'
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return '—'
  return new Intl.DateTimeFormat('es-CO', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  }).format(date)
}

export function formatDateTime(iso: string | null | undefined): string {
  if (!iso) return '—'
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return '—'
  return new Intl.DateTimeFormat('es-CO', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date)
}

export function formatRelative(iso: string | null | undefined): string {
  if (!iso) return '—'
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return '—'
  const seconds = Math.round((date.getTime() - Date.now()) / 1000)
  const rtf = new Intl.RelativeTimeFormat('es-CO', { numeric: 'auto' })
  const steps: [number, Intl.RelativeTimeFormatUnit][] = [
    [60, 'second'],
    [3600, 'minute'],
    [86400, 'hour'],
    [2592000, 'day'],
    [31536000, 'month'],
  ]
  let unitSeconds = 1
  for (const [limit, unit] of steps) {
    if (Math.abs(seconds) < limit) {
      return rtf.format(Math.round(seconds / unitSeconds), unit)
    }
    unitSeconds = limit
  }
  return rtf.format(Math.round(seconds / 31536000), 'year')
}

export function shortHash(hash: string, size = 8): string {
  if (!hash) return '—'
  if (hash === 'GENESIS') return 'GÉNESIS'
  if (hash.length <= size * 2) return hash
  return `${hash.slice(0, size)}…${hash.slice(-4)}`
}

export function formatNumber(value: number, decimals = 0): string {
  return new Intl.NumberFormat('es-CO', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value)
}
