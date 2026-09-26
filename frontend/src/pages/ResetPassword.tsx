import { useState, type FormEvent } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'

import { api } from '../lib/api'
import { useAuth } from '../lib/auth'
import Brand from '../components/Brand'
import { ErrorNote, Field } from '../components/ui'

export default function ResetPassword() {
  const { applySession } = useAuth()
  const [params] = useSearchParams()
  const navigate = useNavigate()
  const token = params.get('token') ?? ''

  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState<unknown>(null)
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)

    if (!token) {
      setError(new Error('El enlace no incluye un token válido. Solicita uno nuevo.'))
      return
    }
    if (password.length < 8) {
      setError(new Error('La contraseña debe tener al menos 8 caracteres.'))
      return
    }
    if (password !== confirm) {
      setError(new Error('Las contraseñas no coinciden.'))
      return
    }

    setSubmitting(true)
    try {
      const result = await api.resetPassword(token, password)
      // El backend deja sesión iniciada: ya demostró control del correo.
      applySession(result)
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
            <h1 className="display display-md">Elegir nueva contraseña</h1>
            {!token && (
              <p className="small" style={{ color: 'var(--danger)', marginTop: 'var(--sp-2)' }}>
                Este enlace no trae un token. Ábrelo desde el correo que recibiste.
              </p>
            )}
          </div>

          <form className="stack stack-4" onSubmit={handleSubmit}>
            {error != null && <ErrorNote error={error} />}

            <Field label="Nueva contraseña" hint="Mínimo 8 caracteres.">
              <input
                className="input"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="new-password"
                required
                minLength={8}
                autoFocus
              />
            </Field>

            <Field label="Confirmar contraseña">
              <input
                className="input"
                type="password"
                value={confirm}
                onChange={(e) => setConfirm(e.target.value)}
                autoComplete="new-password"
                required
                minLength={8}
              />
            </Field>

            <button className="btn btn-primary btn-block" disabled={submitting || !token}>
              {submitting ? <span className="spin" /> : 'Guardar y entrar'}
            </button>
          </form>

          <Link to="/entrar" className="small muted" style={{ textAlign: 'center' }}>
            ← Volver a entrar
          </Link>
        </div>
      </main>
    </div>
  )
}
