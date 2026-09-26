import { Link } from 'react-router-dom'

export default function NotFound() {
  return (
    <div className="full-center">
      <div className="stack stack-4" style={{ textAlign: 'center', maxWidth: 420 }}>
        <span style={{ fontSize: '3rem' }} aria-hidden="true">
          🌾
        </span>
        <h1 className="display display-lg">Esta página no existe</h1>
        <p className="muted">
          El enlace puede estar mal escrito o el recurso fue retirado.
        </p>
        <Link to="/" className="btn btn-primary" style={{ justifySelf: 'center' }}>
          Volver al inicio
        </Link>
      </div>
    </div>
  )
}
