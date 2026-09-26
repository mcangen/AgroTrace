import { useRef, useState, type FormEvent } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'

import { api } from '../lib/api'
import { ErrorNote } from '../components/ui'

interface Message {
  role: 'user' | 'ai'
  text: string
  fromModel?: boolean
}

const SUGGESTIONS = [
  '¿Qué etapas me faltan por registrar en mis lotes?',
  '¿Qué datos me pediría un importador que aún no tengo?',
  'Resume el estado de mi operación en tres puntos.',
  '¿Cuál de mis lotes está más listo para exportar?',
]

export default function Assistant() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [productId, setProductId] = useState<string>('')
  const endRef = useRef<HTMLDivElement>(null)

  const { data: aiStatus } = useQuery({
    queryKey: ['ai-status'],
    queryFn: api.aiStatus,
    staleTime: 5 * 60_000,
  })
  const { data: products } = useQuery({
    queryKey: ['products'],
    queryFn: () => api.listProducts(),
  })

  const ask = useMutation({
    mutationFn: (question: string) =>
      api.askAssistant(question, productId ? Number(productId) : undefined),
    onSuccess: (result) => {
      setMessages((prev) => [
        ...prev,
        { role: 'ai', text: result.answer, fromModel: result.generated_by_ai },
      ])
      requestAnimationFrame(() => endRef.current?.scrollIntoView({ behavior: 'smooth' }))
    },
  })

  function send(question: string) {
    const trimmed = question.trim()
    if (!trimmed || ask.isPending) return
    setMessages((prev) => [...prev, { role: 'user', text: trimmed }])
    setInput('')
    ask.mutate(trimmed)
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    send(input)
  }

  return (
    <div className="stack stack-5" style={{ maxWidth: 820 }}>
      <header className="page-head">
        <div>
          <span className="eyebrow">Agente conversacional</span>
          <h1 className="display display-lg" style={{ marginTop: 'var(--sp-2)' }}>
            Asistente
          </h1>
          <p className="lede" style={{ marginTop: 'var(--sp-2)' }}>
            Responde con el contexto real de tus lotes y su cadena de trazabilidad.
          </p>
        </div>
        {aiStatus && (
          <span className={`badge ${aiStatus.enabled ? 'badge-ai' : 'badge-warn'}`}>
            {aiStatus.enabled ? `✦ ${aiStatus.model}` : '◌ Sin API key'}
          </span>
        )}
      </header>

      <div className="card card-pad stack stack-4">
        <div className="row row-wrap" style={{ gap: 'var(--sp-3)' }}>
          <label className="small muted" htmlFor="ctx">
            Contexto:
          </label>
          <select
            id="ctx"
            className="select"
            style={{ maxWidth: 300 }}
            value={productId}
            onChange={(e) => setProductId(e.target.value)}
          >
            <option value="">Toda mi operación</option>
            {products?.map((product) => (
              <option key={product.id} value={product.id}>
                {product.name} · {product.farm_name}
              </option>
            ))}
          </select>
        </div>

        <div className="chat">
          {messages.length === 0 ? (
            <div className="stack stack-3">
              <p className="muted small">Prueba con una de estas preguntas:</p>
              <div className="row row-wrap" style={{ gap: 'var(--sp-2)' }}>
                {SUGGESTIONS.map((suggestion) => (
                  <button
                    key={suggestion}
                    type="button"
                    className="suggestion"
                    onClick={() => send(suggestion)}
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            messages.map((message, index) => (
              <div
                key={index}
                className={`bubble ${message.role === 'user' ? 'bubble-user' : 'bubble-ai'}`}
              >
                {message.text}
                {message.role === 'ai' && message.fromModel === false && (
                  <div
                    className="small"
                    style={{ marginTop: 'var(--sp-2)', color: 'var(--amber-ink)' }}
                  >
                    ◌ Respuesta de respaldo, sin modelo
                  </div>
                )}
              </div>
            ))
          )}

          {ask.isPending && (
            <div className="bubble bubble-ai row" style={{ gap: 'var(--sp-2)' }}>
              <span className="spin" style={{ color: 'var(--green-600)' }} />
              <span className="muted small">Pensando…</span>
            </div>
          )}
          <div ref={endRef} />
        </div>

        {ask.error != null && <ErrorNote error={ask.error} />}

        <form className="chat-form" onSubmit={handleSubmit}>
          <textarea
            className="textarea"
            style={{ minHeight: 56 }}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                send(input)
              }
            }}
            placeholder="Escribe tu pregunta… (Enter para enviar)"
            aria-label="Pregunta para el asistente"
          />
          <button className="btn btn-primary" disabled={ask.isPending || !input.trim()}>
            Enviar
          </button>
        </form>
      </div>
    </div>
  )
}
