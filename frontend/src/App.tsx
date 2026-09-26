import { Navigate, Route, Routes, useLocation } from 'react-router-dom'
import { Suspense, lazy, type ReactNode } from 'react'

import { useAuth } from './lib/auth'
import AppShell from './components/AppShell'
import Landing from './pages/Landing'
import Login from './pages/Login'
import Register from './pages/Register'
import ForgotPassword from './pages/ForgotPassword'
import ResetPassword from './pages/ResetPassword'
import Directory from './pages/Directory'
import Products from './pages/Products'
import ProductNew from './pages/ProductNew'
import ProductDetail from './pages/ProductDetail'
import CertificationDiagnosis from './pages/CertificationDiagnosis'
import Farms from './pages/Farms'
import Inquiries from './pages/Inquiries'
import Assistant from './pages/Assistant'
import Passport from './pages/Passport'
import NotFound from './pages/NotFound'

// El panel es la única pantalla que usa la librería de gráficas; cargarla aparte
// evita que la landing y el pasaporte público arrastren ese peso.
const Dashboard = lazy(() => import('./pages/Dashboard'))

function FullPageLoader() {
  return (
    <div className="full-center">
      <div className="stack-3" style={{ alignItems: 'center' }}>
        <span className="spin" style={{ fontSize: 24, color: 'var(--green-600)' }} />
        <p className="muted small">Cargando AgroTrace…</p>
      </div>
    </div>
  )
}

/** Exige sesión; recuerda a dónde iba el usuario para volver tras el login. */
function RequireAuth({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth()
  const location = useLocation()

  if (loading) return <FullPageLoader />
  if (!user) return <Navigate to="/entrar" replace state={{ from: location.pathname }} />
  return <>{children}</>
}

/** Login y registro no deben mostrarse a quien ya inició sesión. */
function RedirectIfAuthed({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth()
  if (loading) return <FullPageLoader />
  if (user) return <Navigate to="/panel" replace />
  return <>{children}</>
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/p/:publicId" element={<Passport />} />
      <Route path="/directorio" element={<Directory />} />

      <Route
        path="/entrar"
        element={
          <RedirectIfAuthed>
            <Login />
          </RedirectIfAuthed>
        }
      />
      <Route
        path="/crear-cuenta"
        element={
          <RedirectIfAuthed>
            <Register />
          </RedirectIfAuthed>
        }
      />
      {/* Recuperar/restablecer no se envuelven en RedirectIfAuthed: alguien con
          sesion (quiza expirada o de otro dispositivo) igual debe poder usarlos. */}
      <Route path="/recuperar" element={<ForgotPassword />} />
      <Route path="/restablecer" element={<ResetPassword />} />

      <Route
        element={
          <RequireAuth>
            <AppShell />
          </RequireAuth>
        }
      >
        <Route
          path="/panel"
          element={
            <Suspense fallback={<FullPageLoader />}>
              <Dashboard />
            </Suspense>
          }
        />
        <Route path="/panel/lotes" element={<Products />} />
        <Route path="/panel/lotes/nuevo" element={<ProductNew />} />
        <Route path="/panel/lotes/:id" element={<ProductDetail />} />
        <Route path="/panel/lotes/:id/certificaciones" element={<CertificationDiagnosis />} />
        <Route path="/panel/fincas" element={<Farms />} />
        <Route path="/panel/mensajes" element={<Inquiries />} />
        <Route path="/panel/asistente" element={<Assistant />} />
      </Route>

      <Route path="*" element={<NotFound />} />
    </Routes>
  )
}
