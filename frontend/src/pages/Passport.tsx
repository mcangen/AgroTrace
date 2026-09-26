/** Pasaporte público del producto: la página que abre el QR.
 *
 * Sin sesión y sin menú de aplicación. Está escrita para el comprador, el
 * importador o el turista, no para el productor.
 */

import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'

import { api, passportQrSrc } from '../lib/api'
import ChainTimeline from '../components/ChainTimeline'
import ContactProducerForm from '../components/ContactProducerForm'
import { ChainBadge, ErrorNote, Spinner } from '../components/ui'
import { formatDate, formatDateTime, formatNumber, STATUS_LABELS } from '../lib/format'
import type { CertificationVerdict } from '../lib/types'

type Lang = 'es' | 'en'

const VERDICT_ICON: Record<CertificationVerdict, string> = {
  READY: '🎉',
  ALMOST_READY: '📋',
  NOT_READY: '⚠',
}

export default function Passport() {
  const { publicId } = useParams<{ publicId: string }>()
  const [lang, setLang] = useState<Lang>('es')

  const { data, isLoading, error } = useQuery({
    queryKey: ['passport', publicId],
    queryFn: () => api.passport(publicId!),
    enabled: Boolean(publicId),
  })

  if (isLoading) {
    return (
      <div className="full-center">
        <Spinner label="Abriendo pasaporte…" />
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="full-center">
        <div className="stack stack-4" style={{ maxWidth: 420, textAlign: 'center' }}>
          <h1 className="display display-md">Pasaporte no encontrado</h1>
          <ErrorNote error={error ?? new Error('Este identificador no existe.')} />
          <Link to="/" className="btn btn-secondary">
            Ir a AgroTrace
          </Link>
        </div>
      </div>
    )
  }

  const story = lang === 'es' ? data.story_es : data.story_en
  const sheetTitle = lang === 'es' ? data.export_title_es : data.export_title_en
  const sheetBody = lang === 'es' ? data.export_body_es : data.export_body_en
  const t =
    lang === 'es'
      ? {
          passport: 'Pasaporte del producto',
          origin: 'Historia de origen',
          sheet: 'Ficha de exportación',
          chain: 'Cadena de trazabilidad',
          chainSub: 'Cada evento está sellado con el hash del anterior.',
          farm: 'Finca',
          origin2: 'Origen',
          altitude: 'Altitud',
          variety: 'Variedad',
          status: 'Estado',
          harvest: 'Cosecha',
          planting: 'Siembra',
          events: 'Eventos sellados',
          scan: 'Comparte este pasaporte',
          scanBody: 'Escanea o comparte el código para abrir esta misma página.',
          verifiedBy: 'Verificado por AgroTrace',
          aiNote: 'Texto generado por IA a partir de datos verificados',
          noStory: 'Este lote aún no tiene una narrativa publicada.',
          certifications: 'Certificaciones',
          certAssessed: 'Autoevaluado',
          verdict: {
            READY: 'Listo para auditoría',
            ALMOST_READY: 'Casi listo',
            NOT_READY: 'Preparación en curso',
          } as Record<CertificationVerdict, string>,
        }
      : {
          passport: 'Product passport',
          origin: 'Origin story',
          sheet: 'Export sheet',
          chain: 'Traceability chain',
          chainSub: 'Each event is sealed with the previous event’s hash.',
          farm: 'Farm',
          origin2: 'Origin',
          altitude: 'Altitude',
          variety: 'Variety',
          status: 'Status',
          harvest: 'Harvest',
          planting: 'Planting',
          events: 'Sealed events',
          scan: 'Share this passport',
          scanBody: 'Scan or share the code to open this same page.',
          verifiedBy: 'Verified by AgroTrace',
          aiNote: 'AI-generated text based on verified data',
          noStory: 'This lot has no published narrative yet.',
          certifications: 'Certifications',
          certAssessed: 'Self-assessed',
          verdict: {
            READY: 'Ready for audit',
            ALMOST_READY: 'Almost ready',
            NOT_READY: 'Preparation underway',
          } as Record<CertificationVerdict, string>,
        }

  return (
    <div className="passport-page">
      <header className="passport-hero">
        <div className="passport-wrap stack stack-4">
          <div className="row row-between row-wrap">
            <Link to="/" className="brand brand-on-dark">
              <span className="brand-mark" aria-hidden="true">
                A
              </span>
              AgroTrace
            </Link>
            <div className="lang-switch" role="group" aria-label="Idioma / Language">
              <button
                type="button"
                className={`lang-btn${lang === 'es' ? ' active' : ''}`}
                onClick={() => setLang('es')}
              >
                ES
              </button>
              <button
                type="button"
                className={`lang-btn${lang === 'en' ? ' active' : ''}`}
                onClick={() => setLang('en')}
              >
                EN
              </button>
            </div>
          </div>

          <div>
            <span className="eyebrow eyebrow-light">{t.passport}</span>
            <h1 className="passport-title" style={{ marginTop: 'var(--sp-3)' }}>
              {data.product_name}
            </h1>
            <p
              className="lede"
              style={{ color: 'var(--ink-on-dark-muted)', marginTop: 'var(--sp-2)' }}
            >
              {data.farm_name} · {data.location}
            </p>
          </div>

          <div className="row row-wrap" style={{ gap: 'var(--sp-3)' }}>
            <ChainBadge verification={data.verification} />
            <span className="badge badge-neutral">
              ★ {data.reputation_score.toFixed(1)} / 5
            </span>
          </div>
        </div>
      </header>

      <main className="passport-body stack stack-5">
        <section className="card card-pad">
          <div className="passport-meta">
            <div>
              <div className="passport-meta-label">{t.farm}</div>
              <div className="passport-meta-value">{data.farm_name}</div>
            </div>
            <div>
              <div className="passport-meta-label">{t.origin2}</div>
              <div className="passport-meta-value">{data.location}</div>
            </div>
            {data.variety && (
              <div>
                <div className="passport-meta-label">{t.variety}</div>
                <div className="passport-meta-value">{data.variety}</div>
              </div>
            )}
            {data.altitude_m != null && (
              <div>
                <div className="passport-meta-label">{t.altitude}</div>
                <div className="passport-meta-value">
                  {formatNumber(data.altitude_m)} msnm
                </div>
              </div>
            )}
            <div>
              <div className="passport-meta-label">{t.status}</div>
              <div className="passport-meta-value">{STATUS_LABELS[data.status]}</div>
            </div>
            <div>
              <div className="passport-meta-label">
                {data.harvest_date ? t.harvest : t.planting}
              </div>
              <div className="passport-meta-value">
                {formatDate(data.harvest_date ?? data.planting_date)}
              </div>
            </div>
            <div>
              <div className="passport-meta-label">{t.events}</div>
              <div className="passport-meta-value">
                {formatNumber(data.verification.total_events)}
              </div>
            </div>
          </div>
        </section>

        {data.certifications.length > 0 && (
          <section className="card card-pad stack stack-3">
            <h2 className="display display-sm">{t.certifications}</h2>
            <div className="cert-badge-row">
              {data.certifications.map((cert) => (
                <div
                  className="cert-badge"
                  key={cert.standard}
                  style={{ borderColor: cert.color }}
                >
                  <span className="cert-badge-icon" aria-hidden="true">
                    {cert.badge}
                  </span>
                  <div>
                    <div className="cert-badge-name">{cert.standard_name}</div>
                    <div className="small muted">
                      {VERDICT_ICON[cert.verdict]} {t.verdict[cert.verdict]} ·{' '}
                      {cert.overall_score}%
                    </div>
                    <div className="small faint">
                      {t.certAssessed} · {formatDate(cert.assessed_at)}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        <section className="card card-pad stack stack-3">
          <div className="row row-between row-wrap">
            <h2 className="display display-md">{t.origin}</h2>
            {data.ai_model && <span className="badge badge-ai">✦ {data.ai_model}</span>}
          </div>
          {story ? (
            <>
              <p className="ai-story" style={{ fontSize: '1.15rem' }}>
                {story}
              </p>
              {data.tasting_notes && (
                <p className="small muted">{data.tasting_notes}</p>
              )}
              <p className="small faint">
                {t.aiNote}
                {data.ai_generated_at && ` · ${formatDateTime(data.ai_generated_at)}`}
              </p>
            </>
          ) : (
            <p className="muted">{t.noStory}</p>
          )}
        </section>

        {sheetTitle && sheetBody && (
          <section className="card card-pad stack stack-3">
            <h2 className="display display-md">{t.sheet}</h2>
            <h3 className="display display-sm">{sheetTitle}</h3>
            <p>{sheetBody}</p>
          </section>
        )}

        <section className="card card-pad stack stack-4">
          <div>
            <h2 className="display display-md">{t.chain}</h2>
            <p className="small muted" style={{ marginTop: 4 }}>
              {t.chainSub}
            </p>
          </div>
          {!data.verification.valid && (
            <div className="form-error" role="alert">
              <span aria-hidden="true">⚠</span>
              <span>{data.verification.message}</span>
            </div>
          )}
          <ChainTimeline events={data.events} verification={data.verification} />
        </section>

        <ContactProducerForm publicId={data.public_id} lang={lang} />

        <section className="card card-pad stack stack-3">
          <h2 className="display display-sm">{t.scan}</h2>
          <div className="qr-box">
            <img
              src={passportQrSrc(data.public_id)}
              alt={`QR · ${data.product_name}`}
              width={108}
              height={108}
            />
            <div className="stack stack-2">
              <code className="hash">{data.public_id}</code>
              <span className="small muted">{t.scanBody}</span>
            </div>
          </div>
        </section>

        <p className="small faint" style={{ textAlign: 'center' }}>
          {t.verifiedBy} · {formatDateTime(data.verification.verified_at)}
        </p>
      </main>
    </div>
  )
}
