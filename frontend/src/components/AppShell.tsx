import { useEffect, useState } from 'react'
import { NavLink, Outlet, useLocation } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'

import { api } from '../lib/api'
import { useAuth } from '../lib/auth'
import Brand from './Brand'

const NAV = [
  { to: '/panel', label: 'Panel', icon: '◧', end: true },
  { to: '/panel/lotes', label: 'Lotes', icon: '❏', end: false },
  { to: '/panel/fincas', label: 'Fincas', icon: '⌂', end: false },
  { to: '/panel/mensajes', label: 'Mensajes', icon: '✉', end: false },
  { to: '/panel/asistente', label: 'Asistente', icon: '✦', end: false },
]

export default function AppShell() {
  const { user, logout } = useAuth()
  const location = useLocation()
  const [menuOpen, setMenuOpen] = useState(false)

  const { data: aiStatus } = useQuery({
    queryKey: ['ai-status'],
    queryFn: api.aiStatus,
    staleTime: 5 * 60_000,
  })

  const { data: unreadInquiries } = useQuery({
    queryKey: ['inquiries-unread'],
    queryFn: api.unreadInquiryCount,
    staleTime: 60_000,
  })

  // Navegar en móvil debe cerrar el menú lateral.
  useEffect(() => setMenuOpen(false), [location.pathname])

  const initials = (user?.full_name ?? '?')
    .split(' ')
    .slice(0, 2)
    .map((part) => part[0])
    .join('')
    .toUpperCase()

  return (
    <div className="shell">
      {menuOpen && <div className="scrim" onClick={() => setMenuOpen(false)} />}

      <aside className={`sidebar${menuOpen ? ' open' : ''}`}>
        <Brand to="/panel" onDark />

        <nav className="nav-group" aria-label="Navegación principal">
          <span className="nav-heading">Operación</span>
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}
            >
              <span className="nav-icon" aria-hidden="true">
                {item.icon}
              </span>
              {item.label}
              {item.to === '/panel/mensajes' && !!unreadInquiries && (
                <span className="nav-badge" aria-label={`${unreadInquiries} sin leer`}>
                  {unreadInquiries}
                </span>
              )}
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-footer">
          {aiStatus && (
            <div
              className="small"
              style={{
                color: 'var(--ink-on-dark-faint)',
                padding: '0 0.5rem 0.75rem',
                lineHeight: 1.45,
              }}
            >
              <span
                aria-hidden="true"
                style={{
                  display: 'inline-block',
                  width: 7,
                  height: 7,
                  borderRadius: '50%',
                  marginRight: 6,
                  background: aiStatus.enabled ? 'var(--green-400)' : 'var(--amber)',
                }}
              />
              {aiStatus.enabled ? (
                <>IA activa · {aiStatus.model}</>
              ) : (
                <>IA en modo respaldo</>
              )}
            </div>
          )}

          <div className="user-chip">
            <div className="avatar" aria-hidden="true">
              {initials}
            </div>
            <div className="user-chip-text">
              <div className="user-chip-name">{user?.full_name}</div>
              <div className="user-chip-mail">{user?.email}</div>
            </div>
          </div>
          <button type="button" className="logout-btn" onClick={logout}>
            Cerrar sesión
          </button>
        </div>
      </aside>

      <div className="main">
        <header className="topbar">
          <button
            type="button"
            className="menu-toggle"
            onClick={() => setMenuOpen((open) => !open)}
            aria-label="Abrir menú"
            aria-expanded={menuOpen}
          >
            ☰
          </button>
          <div style={{ flex: 1 }} />
          <NavLink to="/panel/lotes/nuevo" className="btn btn-primary btn-sm">
            + Registrar lote
          </NavLink>
        </header>

        <main className="content">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
