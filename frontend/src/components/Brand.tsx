import { Link } from 'react-router-dom'

export default function Brand({ to = '/', onDark = false }: { to?: string; onDark?: boolean }) {
  return (
    <Link to={to} className={`brand${onDark ? ' brand-on-dark' : ''}`}>
      <span className="brand-mark" aria-hidden="true">
        A
      </span>
      AgroTrace
    </Link>
  )
}
