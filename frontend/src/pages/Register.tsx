import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { useAuth } from '../lib/auth'
import Brand from '../components/Brand'
import { ErrorNote, Field } from '../components/ui'

export default function Register() {
  const { register } = useAuth()
  const navigate = useNavigate()

  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<unknown>(null)
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)

    if (password.length < 8) {
      setError(new Error('La contraseña debe tener al menos 8 caracteres.'))
      return
    }

    setSubmitting(true)
    try {
      await register({ email, password, full_name: fullName })
      navigate('/panel', { replace: true })
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
          “Al entrar te guiamos paso a paso: crear tu primera finca, registrar un lote y
          sellar su primer evento.”
        </blockquote>
        <p className="small" style={{ color: 'var(--ink-on-dark-faint)' }}>
          Trazabilidad criptográfica e IA para pequeños productores del Magdalena.
        </p>
      </aside>

      <main className="auth-main">
        <div className="auth-card stack stack-5">
          <div>
            <h1 className="display display-md">Crear tu cuenta</h1>
            <p className="muted small" style={{ marginTop: 'var(--sp-2)' }}>
              ¿Ya tienes una?{' '}
              <Link to="/entrar" style={{ color: 'var(--green-700)', fontWeight: 600 }}>
                Entrar
              </Link>
            </p>
          </div>

          <form className="stack stack-4" onSubmit={handleSubmit}>
            {error != null && <ErrorNote error={error} />}

            <Field label="Tu nombre completo">
              <input
                className="input"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                autoComplete="name"
                required
                minLength={2}
              />
            </Field>

            <Field label="Correo electrónico">
              <input
                className="input"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoComplete="email"
                required
              />
            </Field>

            <Field label="Contraseña" hint="Mínimo 8 caracteres.">
              <input
                className="input"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="new-password"
                required
                minLength={8}
              />
            </Field>

            <button className="btn btn-primary btn-block" disabled={submitting}>
              {submitting ? <span className="spin" /> : 'Crear cuenta'}
            </button>
          </form>

          <Link to="/" className="small muted" style={{ textAlign: 'center' }}>
            ← Volver al inicio
          </Link>
        </div>
      </main>
    </div>
  )
}
