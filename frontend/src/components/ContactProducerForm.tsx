/** Formulario de contacto del pasaporte público: un comprador le escribe al
 * productor sin necesitar cuenta.
 *
 * Es el único punto de escritura sin sesión de toda la app, así que la vista
 * confirma y se cierra en vez de dejar el formulario abierto: reduce envíos
 * repetidos por error (el backend además limita por IP).
 */

import { useState, type FormEvent } from 'react'
import { useMutation } from '@tanstack/react-query'

import { api } from '../lib/api'
import { ErrorNote, Field } from './ui'

type Lang = 'es' | 'en'

const COPY = {
  es: {
    title: 'Contactar al productor',
    intro: 'Escríbele directamente sobre este lote. Recibirá tu mensaje en su panel.',
    name: 'Tu nombre',
    email: 'Tu correo',
    country: 'País (opcional)',
    message: 'Mensaje',
    placeholder: 'Nos interesa este producto. ¿Podríamos recibir información de precios y volúmenes disponibles?',
    send: 'Enviar mensaje',
    sent: '✓ Mensaje enviado',
    sentBody: 'El productor recibió tu mensaje y podrá responderte a tu correo.',
    again: 'Enviar otro mensaje',
    hint: 'Mínimo 10 caracteres.',
  },
  en: {
    title: 'Contact the producer',
    intro: 'Write directly about this lot. They will receive your message in their dashboard.',
    name: 'Your name',
    email: 'Your email',
    country: 'Country (optional)',
    message: 'Message',
    placeholder: 'We are interested in this product. Could we get pricing and available volumes?',
    send: 'Send message',
    sent: '✓ Message sent',
    sentBody: 'The producer received your message and can reply to your email.',
    again: 'Send another message',
    hint: 'At least 10 characters.',
  },
} as const

export default function ContactProducerForm({
  publicId,
  lang,
}: {
  publicId: string
  lang: Lang
}) {
  const t = COPY[lang]
  const [form, setForm] = useState({
    buyer_name: '',
    buyer_email: '',
    buyer_country: '',
    message: '',
  })

  const send = useMutation({
    mutationFn: () =>
      api.sendInquiry(publicId, {
        buyer_name: form.buyer_name.trim(),
        buyer_email: form.buyer_email.trim(),
        buyer_country: form.buyer_country.trim() || null,
        message: form.message.trim(),
      }),
  })

  function update(field: keyof typeof form, value: string) {
    setForm((prev) => ({ ...prev, [field]: value }))
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    send.mutate()
  }

  if (send.isSuccess) {
    return (
      <section className="card card-pad stack stack-3">
        <h2 className="display display-md">{t.sent}</h2>
        <p className="muted">{t.sentBody}</p>
        <button
          type="button"
          className="btn btn-secondary"
          style={{ alignSelf: 'flex-start' }}
          onClick={() => {
            setForm({ buyer_name: '', buyer_email: '', buyer_country: '', message: '' })
            send.reset()
          }}
        >
          {t.again}
        </button>
      </section>
    )
  }

  return (
    <section className="card card-pad stack stack-4">
      <div>
        <h2 className="display display-md">{t.title}</h2>
        <p className="small muted" style={{ marginTop: 'var(--sp-2)' }}>
          {t.intro}
        </p>
      </div>

      <form className="stack stack-4" onSubmit={handleSubmit}>
        {send.error != null && <ErrorNote error={send.error} />}

        <div className="form-grid">
          <Field label={t.name}>
            <input
              className="input"
              value={form.buyer_name}
              onChange={(e) => update('buyer_name', e.target.value)}
              required
              minLength={2}
              autoComplete="name"
            />
          </Field>
          <Field label={t.email}>
            <input
              className="input"
              type="email"
              value={form.buyer_email}
              onChange={(e) => update('buyer_email', e.target.value)}
              required
              autoComplete="email"
            />
          </Field>
          <Field label={t.country}>
            <input
              className="input"
              value={form.buyer_country}
              onChange={(e) => update('buyer_country', e.target.value)}
              autoComplete="country-name"
            />
          </Field>
        </div>

        <Field label={t.message} hint={t.hint}>
          <textarea
            className="textarea"
            style={{ minHeight: 110 }}
            value={form.message}
            onChange={(e) => update('message', e.target.value)}
            placeholder={t.placeholder}
            required
            minLength={10}
            maxLength={2000}
          />
        </Field>

        <button
          className="btn btn-primary"
          style={{ alignSelf: 'flex-start' }}
          disabled={send.isPending}
        >
          {send.isPending ? <span className="spin" /> : t.send}
        </button>
      </form>
    </section>
  )
}
