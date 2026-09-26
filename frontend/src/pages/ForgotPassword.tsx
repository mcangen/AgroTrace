import { useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'

import { api } from '../lib/api'
import Brand from '../components/Brand'
import { ErrorNote, Field } from '../components/ui'

export default function ForgotPassword() {
  const [email, setEmail] = useState('')
  const [error, setError] = useState<unknown>(null)
  const [submitting, setSubmitting] = useState(false)
  const [sent, setSent] = useState(false)

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await api.forgotPassword(email)
      // El backend responde igual exista o no la cuenta; la UI hace lo mismo.
      setSent(true)
    } catch (err) {
      setError(err)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="auth">
      <aside className="auth-aside">
        <Brand onDark />
        <blockquote className="auth-quote">
          “Detrás de cada producto hay una historia de tierra, familia y trabajo. AgroTrace
          la hace verificable.”
        </blockquote>
        <p className="small" style={{ color: 'var(--ink-on-dark-faint)' }}>
          Trazabilidad criptográfica e IA para pequeños productores del Magdalena.
        </p>
      </aside>

      <main className="auth-main">
        <div className="auth-card stack stack-5">
          {sent ? (
            <div className="stack stack-4">
              <h1 className="display display-md">Revisa tu correo</h1>
              <p className="muted">
                Si <strong>{email}</strong> tiene una cuenta, te enviamos un enlace para
                restablecer tu contraseña. Vence en una hora.
              </p>
              <Link to="/entrar" className="btn btn-secondary" style={{ alignSelf: 'flex-start' }}>
                Volver a entrar
              </Link>
            </div>
          ) : (
            <>
              <div>
                <h1 className="display display-md">Recuperar contraseña</h1>
                <p className="muted small" style={{ marginTop: 'var(--sp-2)' }}>
                  Te enviaremos un enlace a tu correo para elegir una nueva.
                </p>
              </div>

              <form className="stack stack-4" onSubmit={handleSubmit}>
                {error != null && <ErrorNote error={error} />}

                <Field label="Correo electrónico">
                  <input
                    className="input"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    autoComplete="email"
                    required
                    autoFocus
                  />
                </Field>

                <button className="btn btn-primary btn-block" disabled={submitting}>
                  {submitting ? <span className="spin" /> : 'Enviar enlace'}
                </button>
              </form>
            </>
          )}

          <Link to="/entrar" className="small muted" style={{ textAlign: 'center' }}>
            ← Volver a entrar
          </Link>
        </div>
      </main>
    </div>
  )
}
