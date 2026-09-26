/** Diagnóstico de certificación de un lote: selector de estándar, cuestionario
 * y resultado con hoja de ruta. Privado — nada de esto llega al pasaporte
 * público del producto. */

import { useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient, type UseQueryResult } from '@tanstack/react-query'

import { api } from '../lib/api'
import CertQuestionCard from '../components/CertQuestionCard'
import CertResult from '../components/CertResult'
import { ErrorNote, Spinner } from '../components/ui'
import { CERT_VERDICT_LABELS, formatDate, formatRelative } from '../lib/format'
import type {
  CertificationAssessment,
  CertificationStandard,
  CertStandardDef,
} from '../lib/types'

type Stage = 'select' | 'wizard' | 'result'

type FlatQuestion = CertStandardDef['sections'][number]['questions'][number] & {
  sectionName: string
}

export default function CertificationDiagnosis() {
  const { id } = useParams<{ id: string }>()
  const productId = Number(id)
  const queryClient = useQueryClient()

  const [stage, setStage] = useState<Stage>('select')
  const [standardKey, setStandardKey] = useState<CertificationStandard | null>(null)
  const [answers, setAnswers] = useState<Record<string, string>>({})
  const [currentIndex, setCurrentIndex] = useState(0)
  const [result, setResult] = useState<CertificationAssessment | null>(null)

  const productQuery = useQuery({
    queryKey: ['product', productId],
    queryFn: () => api.getProduct(productId),
    enabled: Number.isFinite(productId),
  })

  const standardsQuery = useQuery({
    queryKey: ['cert-standards'],
    queryFn: api.listCertStandards,
    staleTime: Infinity,
  })

  // Solo hay dos estándares en esta versión; se consultan directo en vez de
  // armar un loop dinámico de queries para un conjunto que no va a crecer aquí.
  const latestFairtrade = useQuery({
    queryKey: ['cert-latest', productId, 'FAIRTRADE'],
    queryFn: () => api.latestCertAssessment(productId, 'FAIRTRADE'),
    enabled: Number.isFinite(productId),
  })
  const latestRainforest = useQuery({
    queryKey: ['cert-latest', productId, 'RAINFOREST_ALLIANCE'],
    queryFn: () => api.latestCertAssessment(productId, 'RAINFOREST_ALLIANCE'),
    enabled: Number.isFinite(productId),
  })
  const latestByStandard: Record<CertificationStandard, CertificationAssessment | null | undefined> = {
    FAIRTRADE: latestFairtrade.data,
    RAINFOREST_ALLIANCE: latestRainforest.data,
  }

  const historyQuery = useQuery({
    queryKey: ['cert-history', productId, standardKey],
    queryFn: () => api.listCertAssessments(productId, standardKey!),
    enabled: standardKey != null,
  })

  const submit = useMutation({
    mutationFn: () => api.submitCertAssessment(productId, standardKey!, answers),
    onSuccess: (assessment) => {
      setResult(assessment)
      setStage('result')
      queryClient.invalidateQueries({ queryKey: ['cert-history', productId, standardKey] })
      queryClient.invalidateQueries({ queryKey: ['cert-latest', productId, standardKey] })
    },
  })

  const standardDef = useMemo(
    () => standardsQuery.data?.find((s) => s.key === standardKey) ?? null,
    [standardsQuery.data, standardKey],
  )

  const flatQuestions: FlatQuestion[] = useMemo(
    () =>
      standardDef?.sections.flatMap((section) =>
        section.questions.map((question) => ({ ...question, sectionName: section.name })),
      ) ?? [],
    [standardDef],
  )

  const current = flatQuestions[currentIndex]

  function startWizard(key: CertificationStandard) {
    setStandardKey(key)
    setAnswers({})
    setCurrentIndex(0)
    setResult(null)
    setStage('wizard')
  }

  function viewLatest(key: CertificationStandard, assessment: CertificationAssessment) {
    setStandardKey(key)
    setResult(assessment)
    setStage('result')
  }

  function answer(value: string) {
    if (!current) return
    setAnswers((prev) => ({ ...prev, [current.id]: value }))
  }

  function goNext() {
    if (currentIndex < flatQuestions.length - 1) {
      setCurrentIndex((i) => i + 1)
    } else {
      submit.mutate()
    }
  }

  function goPrev() {
    if (currentIndex > 0) setCurrentIndex((i) => i - 1)
  }

  function retry() {
    setAnswers({})
    setCurrentIndex(0)
    setResult(null)
    setStage('wizard')
  }

  if (!Number.isFinite(productId)) return <ErrorNote error={new Error('Lote inválido.')} />

  const progressPct = flatQuestions.length
    ? Math.round(((currentIndex + 1) / flatQuestions.length) * 100)
    : 0

  return (
    <div className="stack stack-5" style={{ maxWidth: 760 }}>
      <header>
        <Link to={`/panel/lotes/${productId}`} className="small muted">
          ← Volver al lote
        </Link>
        <h1 className="display display-lg" style={{ marginTop: 'var(--sp-2)' }}>
          Diagnóstico de certificación
        </h1>
        <p className="lede" style={{ marginTop: 'var(--sp-2)' }}>
          Privado: solo tú ves este resultado. Nada de esto se publica en el pasaporte
          del lote.
        </p>
      </header>

      {stage === 'select' && (
        <StandardSelector
          standardsQuery={standardsQuery}
          latestByStandard={latestByStandard}
          onStart={startWizard}
          onViewLatest={viewLatest}
        />
      )}

      {stage === 'wizard' && standardDef && current && (
        <div className="stack stack-4">
          <div
            className="bar-track"
            role="img"
            aria-label={`Progreso: pregunta ${currentIndex + 1} de ${flatQuestions.length}`}
          >
            <div className="bar-fill" style={{ width: `${progressPct}%` }} />
          </div>

          <CertQuestionCard
            question={current}
            sectionName={current.sectionName}
            index={currentIndex}
            total={flatQuestions.length}
            value={answers[current.id]}
            onAnswer={answer}
          />

          {submit.error != null && <ErrorNote error={submit.error} />}

          <div className="row row-between">
            <button className="btn btn-ghost" onClick={goPrev} disabled={currentIndex === 0}>
              ← Anterior
            </button>
            <button
              className="btn btn-primary"
              onClick={goNext}
              disabled={!answers[current.id] || submit.isPending}
            >
              {submit.isPending ? (
                <span className="spin" />
              ) : currentIndex === flatQuestions.length - 1 ? (
                'Ver diagnóstico →'
              ) : (
                'Siguiente →'
              )}
            </button>
          </div>
        </div>
      )}

      {stage === 'result' && result && productQuery.data && (
        <CertResult
          assessment={result}
          productId={productId}
          publicId={productQuery.data.public_id}
          published={productQuery.data.published_certification_standards.includes(
            result.standard,
          )}
          onRetry={retry}
        />
      )}

      {stage !== 'wizard' && standardKey && (historyQuery.data?.length ?? 0) > 1 && (
        <details className="card card-pad">
          <summary className="chart-title" style={{ cursor: 'pointer' }}>
            Historial de intentos
          </summary>
          <div className="stack stack-2" style={{ marginTop: 'var(--sp-3)' }}>
            {historyQuery.data!.map((attempt) => (
              <div className="row row-between" key={attempt.id}>
                <span className="small muted">{formatDate(attempt.created_at)}</span>
                <span className="small">
                  {attempt.overall_score}% · {CERT_VERDICT_LABELS[attempt.verdict]}
                </span>
              </div>
            ))}
          </div>
        </details>
      )}
    </div>
  )
}

function StandardSelector({
  standardsQuery,
  latestByStandard,
  onStart,
  onViewLatest,
}: {
  standardsQuery: UseQueryResult<CertStandardDef[]>
  latestByStandard: Record<CertificationStandard, CertificationAssessment | null | undefined>
  onStart: (key: CertificationStandard) => void
  onViewLatest: (key: CertificationStandard, assessment: CertificationAssessment) => void
}) {
  if (standardsQuery.isLoading) return <Spinner label="Cargando estándares…" />
  if (standardsQuery.error) return <ErrorNote error={standardsQuery.error} />

  return (
    <div className="stack stack-4">
      <p className="lede">Elige el estándar que quieres evaluar.</p>
      <div className="product-grid">
        {standardsQuery.data?.map((standard) => (
          <StandardCard
            key={standard.key}
            standard={standard}
            latest={latestByStandard[standard.key]}
            onStart={() => onStart(standard.key)}
            onViewLatest={(assessment) => onViewLatest(standard.key, assessment)}
          />
        ))}
      </div>
    </div>
  )
}

function StandardCard({
  standard,
  latest,
  onStart,
  onViewLatest,
}: {
  standard: CertStandardDef
  latest: CertificationAssessment | null | undefined
  onStart: () => void
  onViewLatest: (assessment: CertificationAssessment) => void
}) {
  return (
    <article
      className={`card card-pad cert-standard-card${latest ? ' active' : ''}`}
      style={latest ? { borderColor: standard.color } : undefined}
    >
      <div className="row" style={{ gap: 'var(--sp-3)' }}>
        <span className="cert-standard-badge" aria-hidden="true">
          {standard.badge}
        </span>
        <div>
          <h2 className="product-card-name">{standard.name}</h2>
          <p className="small muted">{standard.total_questions} preguntas</p>
        </div>
      </div>

      {latest ? (
        <div className="stack stack-3" style={{ marginTop: 'var(--sp-4)' }}>
          <p className="small muted">
            Último intento: <strong>{latest.overall_score}%</strong> ·{' '}
            {formatRelative(latest.created_at)}
          </p>
          <div className="row" style={{ gap: 'var(--sp-2)' }}>
            <button className="btn btn-secondary btn-sm" onClick={() => onViewLatest(latest)}>
              Ver resultado
            </button>
            <button className="btn btn-primary btn-sm" onClick={onStart}>
              Repetir
            </button>
          </div>
        </div>
      ) : (
        <button className="btn btn-primary" style={{ marginTop: 'var(--sp-4)' }} onClick={onStart}>
          Comenzar diagnóstico →
        </button>
      )}
    </article>
  )
}
