import { useState, type FormEvent } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'

import { useAuth } from '../lib/auth'
import Brand from '../components/Brand'
import { ErrorNote, Field } from '../components/ui'

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<unknown>(null)
  const [submitting, setSubmitting] = useState(false)

  const redirectTo = (location.state as { from?: string } | null)?.from ?? '/panel'

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await login(email, password)
      navigate(redirectTo, { replace: true })
    } catch (err) {
      setError(err)
    } finally {
      setSubmitting(false)
    }
  }

  function fillDemo() {
    setEmail('demo@agrotrace.co')
    setPassword('agrotrace2026')
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
          <div>
            <h1 className="display display-md">Entrar a tu panel</h1>
            <p className="muted small" style={{ marginTop: 'var(--sp-2)' }}>
              ¿Aún no tienes cuenta?{' '}
              <Link to="/crear-cuenta" style={{ color: 'var(--green-700)', fontWeight: 600 }}>
                Crear una
              </Link>
            </p>
          </div>

          <div className="demo-hint">
            <strong>Cuenta de demostración</strong>
            <br />
            demo@agrotrace.co · agrotrace2026{' '}
            <button
              type="button"
              className="btn btn-ghost btn-sm"
              style={{ padding: '0.15rem 0.5rem', color: 'inherit' }}
              onClick={fillDemo}
            >
              Usar
            </button>
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
              />
            </Field>

            <Field label="Contraseña">
              <input
                className="input"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
                required
              />
            </Field>

            <Link
              to="/recuperar"
              className="small"
              style={{ color: 'var(--green-700)', fontWeight: 600, alignSelf: 'flex-end' }}
            >
              ¿Olvidaste tu contraseña?
            </Link>

            <button className="btn btn-primary btn-block" disabled={submitting}>
              {submitting ? <span className="spin" /> : 'Entrar'}
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
