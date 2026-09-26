/** Guía de primeros pasos: aparece en el panel hasta que el productor conoce
 * las piezas centrales de la app, o hasta que la cierra.
 *
 * Tres pasos se marcan solos con datos reales (crear finca, registrar lote,
 * sellar un evento); los otros tres (pasaporte, mensajes, asistente) se
 * marcan al hacer clic en su propio enlace — no hay una señal de "ya lo viste"
 * más confiable que esa sin instrumentar cada pantalla.
 */

import { useState } from 'react'
import { Link } from 'react-router-dom'

import type { DashboardSummary } from '../lib/types'

const SEEN_KEY = 'agrotrace.onboarding.seen'
const DISMISSED_KEY = 'agrotrace.onboarding.dismissed'

type SeenItem = 'passport' | 'messages' | 'assistant'

function readSeen(): Set<SeenItem> {
  try {
    const raw = localStorage.getItem(SEEN_KEY)
    return new Set(raw ? (JSON.parse(raw) as SeenItem[]) : [])
  } catch {
    return new Set()
  }
}

function markSeen(item: SeenItem) {
  try {
    const seen = readSeen()
    seen.add(item)
    localStorage.setItem(SEEN_KEY, JSON.stringify([...seen]))
  } catch {
    /* almacenamiento bloqueado: no es crítico, el paso simplemente no queda marcado */
  }
}

function readDismissed(): boolean {
  try {
    return localStorage.getItem(DISMISSED_KEY) === '1'
  } catch {
    return false
  }
}

function dismiss() {
  try {
    localStorage.setItem(DISMISSED_KEY, '1')
  } catch {
    /* ignorar */
  }
}

interface Step {
  key: string
  title: string
  body: string
  done: boolean
  cta: string
  to: string
  external?: boolean
  onNavigate?: () => void
}

export default function OnboardingChecklist({ summary }: { summary: DashboardSummary }) {
  const [dismissed, setDismissed] = useState(readDismissed)
  const [seen, setSeen] = useState(readSeen)

  function handleSeen(item: SeenItem) {
    markSeen(item)
    setSeen(readSeen())
  }

  if (dismissed) return null

  const steps: Step[] = [
    {
      key: 'farm',
      title: 'Crea tu primera finca',
      body: 'Una finca agrupa tus lotes y su ubicación. Es lo primero que necesitas para empezar.',
      done: summary.farm_count > 0,
      cta: 'Crear finca',
      to: '/panel/fincas',
    },
    {
      key: 'product',
      title: 'Registra tu primer lote',
      body: 'Un lote es una cosecha o partida que vas a trazar de principio a fin. Al guardarlo, su primer evento ya queda sellado.',
      done: summary.product_count > 0,
      cta: 'Registrar lote',
      to: '/panel/lotes/nuevo',
    },
    {
      key: 'seal',
      title: 'Sella un evento en la cadena',
      body: 'Cada evento (siembra, cosecha, secado…) se sella con un hash SHA-256 que depende del evento anterior. Si alguien altera uno pasado, la cadena completa deja de coincidir y se detecta al instante.',
      done: summary.event_count > summary.product_count,
      cta: 'Ver mis lotes',
      to: '/panel/lotes',
    },
    {
      key: 'passport',
      title: 'Descubre el pasaporte público',
      body: 'Cada lote tiene una página pública con su propio QR: ahí un comprador ve la historia del producto, la cadena verificada, y puede escribirte.',
      done: seen.has('passport'),
      cta: 'Ver mis lotes',
      to: '/panel/lotes',
      onNavigate: () => handleSeen('passport'),
    },
    {
      key: 'messages',
      title: 'Revisa tu bandeja de mensajes',
      body: 'Cuando alguien te escribe desde el pasaporte público de un lote, el mensaje llega aquí (y a tu correo, si lo configuraste).',
      done: seen.has('messages'),
      cta: 'Ir a mensajes',
      to: '/panel/mensajes',
      onNavigate: () => handleSeen('messages'),
    },
    {
      key: 'assistant',
      title: 'Habla con el asistente',
      body: 'Responde preguntas sobre tu operación usando solo tus datos reales: qué lotes tienes, qué te falta registrar, cuál está más listo para exportar.',
      done: seen.has('assistant'),
      cta: 'Abrir asistente',
      to: '/panel/asistente',
      onNavigate: () => handleSeen('assistant'),
    },
  ]

  const doneCount = steps.filter((s) => s.done).length
  const allDone = doneCount === steps.length
  const pct = Math.round((doneCount / steps.length) * 100)

  function handleDismiss() {
    dismiss()
    setDismissed(true)
  }

  if (allDone) {
    return (
      <div className="card card-pad onboarding-done">
        <div className="row row-between row-wrap">
          <span className="small" style={{ fontWeight: 600 }}>
            🎉 Ya conoces todo lo esencial de AgroTrace.
          </span>
          <button type="button" className="btn btn-ghost btn-sm" onClick={handleDismiss}>
            Ocultar
          </button>
        </div>
      </div>
    )
  }

  return (
    <section className="card card-pad onboarding-card">
      <div className="row row-between row-wrap" style={{ alignItems: 'flex-start' }}>
        <div>
          <span className="eyebrow">Primeros pasos</span>
          <h2 className="display display-sm" style={{ marginTop: 'var(--sp-1)' }}>
            Vamos a conocer AgroTrace
          </h2>
        </div>
        <button
          type="button"
          className="btn btn-ghost btn-sm"
          onClick={handleDismiss}
          aria-label="Ocultar guía de primeros pasos"
        >
          ✕
        </button>
      </div>

      <div style={{ margin: 'var(--sp-4) 0' }}>
        <div
          className="bar-track"
          role="img"
          aria-label={`${doneCount} de ${steps.length} pasos completados`}
        >
          <div className="bar-fill" style={{ width: `${pct}%` }} />
        </div>
        <p className="small muted" style={{ marginTop: 'var(--sp-2)' }}>
          {doneCount} de {steps.length} pasos completados
        </p>
      </div>

      <div className="onboarding-steps">
        {steps.map((step) => (
          <OnboardingStep key={step.key} step={step} />
        ))}
      </div>
    </section>
  )
}

function OnboardingStep({ step }: { step: Step }) {
  return (
    <div className={`onboarding-step${step.done ? ' done' : ''}`}>
      <span className="onboarding-check" aria-hidden="true">
        {step.done ? '✓' : ''}
      </span>
      <div className="onboarding-step-body">
        <div className="onboarding-step-title">{step.title}</div>
        <p className="small muted">{step.body}</p>
      </div>
      {!step.done && (
        <Link to={step.to} className="btn btn-secondary btn-sm" onClick={step.onNavigate}>
          {step.cta}
        </Link>
      )}
    </div>
  )
}
