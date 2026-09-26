import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'

import { api } from '../lib/api'
import Brand from '../components/Brand'

const STEPS = [
  {
    num: '01',
    title: 'Registra lo que pasa en campo',
    body: 'Siembra, fertilización, cosecha, secado, empaque — con fotos como evidencia si quieres. Cada evento se sella con un hash SHA-256 que depende del evento anterior.',
  },
  {
    num: '02',
    title: 'La IA construye la narrativa',
    body: 'Agentes sobre Gemini leen la cadena verificada y redactan la historia de origen, la ficha de exportación bilingüe y el análisis agronómico.',
  },
  {
    num: '03',
    title: 'El comprador lo verifica',
    body: 'Un QR abre el pasaporte público del lote. Cualquiera puede recalcular la cadena, ver si algo fue alterado y escribirle directo al productor.',
  },
]

const AGENTS = [
  {
    icon: '✍️',
    name: 'Agente de narrativa',
    body: 'Escribe la historia de origen en español e inglés usando solo datos verificados de la cadena. Sin inventar certificaciones ni cifras.',
  },
  {
    icon: '📋',
    name: 'Agente de exportación',
    body: 'Produce la ficha técnica bilingüe con variedad, altitud, proceso y rendimiento, lista para un importador.',
  },
  {
    icon: '🔬',
    name: 'Agente agronómico',
    body: 'Detecta vacíos de registro e intervalos anómalos entre etapas, y propone qué mejorar en el siguiente ciclo.',
  },
  {
    icon: '🏅',
    name: 'Agente de certificación',
    body: 'Cruza un diagnóstico de Fairtrade o Rainforest Alliance con tu cadena real y escribe una hoja de ruta personalizada, no genérica.',
  },
  {
    icon: '✦',
    name: 'Asistente',
    body: 'Responde preguntas abiertas sobre tus lotes con el contexto real de tu operación.',
  },
]

const TOOLS = [
  {
    icon: '📷',
    name: 'Evidencia fotográfica',
    body: 'Cada foto se sella junto a su evento: la huella entra al hash. Si alguien sustituye el archivo, se detecta al instante.',
  },
  {
    icon: '📄',
    name: 'Reporte descargable',
    body: 'Ficha del lote, cadena completa y hashes en un PDF listo para enviar a un importador.',
  },
  {
    icon: '🌦',
    name: 'Alertas climáticas',
    body: 'Pronóstico a 7 días por finca, con avisos de lluvia fuerte, calor extremo o riesgo de helada.',
  },
  {
    icon: '✉️',
    name: 'Contacto directo',
    body: 'Un comprador escribe desde el pasaporte público; el mensaje llega a tu bandeja, sin intermediarios.',
  },
]

export default function Landing() {
  const { data: aiStatus } = useQuery({
    queryKey: ['ai-status'],
    queryFn: api.aiStatus,
    staleTime: 5 * 60_000,
  })

  return (
    <>
      <nav className="landing-nav">
        <Brand onDark />
        <div className="row" style={{ gap: 'var(--sp-3)' }}>
          <Link
            to="/directorio"
            className="small"
            style={{ color: 'var(--ink-on-dark-muted)' }}
          >
            Directorio
          </Link>
          <Link to="/entrar" className="btn btn-outline-dark btn-sm">
            Entrar
          </Link>
          <Link to="/crear-cuenta" className="btn btn-on-dark btn-sm">
            Crear cuenta
          </Link>
        </div>
      </nav>

      <header className="hero">
        <div className="hero-inner">
          <div className="stack stack-5">
            <span className="hero-badge">
              🌱 Agroturismo verificable · Magdalena, Colombia
            </span>

            <h1 className="hero-title">
              Cada cosecha cuenta una historia
              <br />
              que el mundo puede <em>verificar</em>.
            </h1>

            <p className="hero-sub">
              AgroTrace le da a pequeños productores una identidad digital, una cadena de
              trazabilidad criptográfica y una narrativa de exportación generada por IA a
              partir de datos reales del campo.
            </p>

            <div className="row row-wrap" style={{ gap: 'var(--sp-3)' }}>
              <Link to="/crear-cuenta" className="btn btn-on-dark btn-lg">
                Registrar mi finca
              </Link>
              <Link to="/entrar" className="btn btn-outline-dark btn-lg">
                Ver la demostración
              </Link>
            </div>

            <div className="row row-wrap" style={{ gap: 'var(--sp-4)', marginTop: 4 }}>
              <span className="small" style={{ color: 'var(--ink-on-dark-faint)' }}>
                🔐 Cadena SHA-256 recalculable
              </span>
              <span className="small" style={{ color: 'var(--ink-on-dark-faint)' }}>
                ✦ {aiStatus?.enabled ? `Gemini ${aiStatus.model}` : 'Agentes sobre Gemini'}
              </span>
              <span className="small" style={{ color: 'var(--ink-on-dark-faint)' }}>
                🌍 Pasaporte público ES / EN
              </span>
            </div>
          </div>

          <aside className="hero-card" aria-label="Ejemplo de pasaporte de producto">
            <div className="row row-between" style={{ marginBottom: 'var(--sp-3)' }}>
              <span className="eyebrow">Pasaporte del lote</span>
              <span className="badge badge-ok">✓ Cadena íntegra</span>
            </div>
            <h2 className="display display-sm" style={{ marginBottom: 'var(--sp-3)' }}>
              Cacao fino de aroma
            </h2>
            <div className="hero-card-row">
              <span className="muted">Finca</span>
              <strong>La Esperanza</strong>
            </div>
            <div className="hero-card-row">
              <span className="muted">Origen</span>
              <strong>Ciénaga, Magdalena</strong>
            </div>
            <div className="hero-card-row">
              <span className="muted">Altitud</span>
              <strong>600 msnm</strong>
            </div>
            <div className="hero-card-row">
              <span className="muted">Eventos sellados</span>
              <strong>8</strong>
            </div>
            <div
              style={{
                marginTop: 'var(--sp-4)',
                paddingTop: 'var(--sp-3)',
                borderTop: '1px dashed var(--line)',
              }}
            >
              <div className="eyebrow" style={{ marginBottom: 4 }}>
                Último sello
              </div>
              <code className="hash">a1f3c9…2db4</code>
            </div>
          </aside>
        </div>
      </header>

      <section className="section">
        <div className="section-inner">
          <span className="eyebrow">Cómo funciona</span>
          <h2 className="display display-lg" style={{ marginTop: 'var(--sp-2)' }}>
            De la finca al mercado global,
            <br />
            sin perder el rastro.
          </h2>
          <div className="feature-grid">
            {STEPS.map((step) => (
              <article className="feature" key={step.num}>
                <div className="feature-num">{step.num}</div>
                <h3 className="feature-title">{step.title}</h3>
                <p className="feature-body">{step.body}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="section section-dark">
        <div className="section-inner">
          <span className="eyebrow eyebrow-light">Agentes de IA</span>
          <h2
            className="display display-lg"
            style={{ marginTop: 'var(--sp-2)', color: 'var(--ink-on-dark)' }}
          >
            Cinco agentes. Un solo registro
            <br />
            del agricultor.
          </h2>
          <p
            className="lede"
            style={{ color: 'var(--ink-on-dark-muted)', maxWidth: '58ch', marginTop: 'var(--sp-3)' }}
          >
            Los agentes solo reciben datos que ya fueron sellados en la cadena. Si un dato no
            está registrado, el modelo lo omite en lugar de estimarlo.
          </p>
          <div className="feature-grid">
            {AGENTS.map((agent) => (
              <article className="feature feature-dark" key={agent.name}>
                <span style={{ fontSize: '1.6rem' }} aria-hidden="true">
                  {agent.icon}
                </span>
                <h3 className="feature-title" style={{ marginTop: 'var(--sp-3)' }}>
                  {agent.name}
                </h3>
                <p className="feature-body">{agent.body}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="section">
        <div className="section-inner">
          <span className="eyebrow">Más allá de los agentes</span>
          <h2 className="display display-lg" style={{ marginTop: 'var(--sp-2)' }}>
            Herramientas para el día a día,
            <br />
            no solo para la demo.
          </h2>
          <div className="feature-grid">
            {TOOLS.map((tool) => (
              <article className="feature" key={tool.name}>
                <span style={{ fontSize: '1.6rem' }} aria-hidden="true">
                  {tool.icon}
                </span>
                <h3 className="feature-title" style={{ marginTop: 'var(--sp-3)' }}>
                  {tool.name}
                </h3>
                <p className="feature-body">{tool.body}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="section section-cream">
        <div className="section-inner" style={{ textAlign: 'center' }}>
          <h2 className="display display-lg">Tu finca merece ser conocida en el mundo.</h2>
          <p
            className="lede"
            style={{ margin: 'var(--sp-4) auto var(--sp-5)', maxWidth: '52ch' }}
          >
            Crea tu cuenta, registra tu primer lote y obtén un pasaporte público verificable
            en menos de cinco minutos.
          </p>
          <Link to="/crear-cuenta" className="btn btn-primary btn-lg">
            Empezar ahora
          </Link>
        </div>
      </section>

      <footer className="landing-footer">
        AgroTrace · Trazabilidad agrícola verificable · Magdalena, Colombia
      </footer>
    </>
  )
}
