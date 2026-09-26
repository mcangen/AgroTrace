/** Una pregunta del cuestionario de certificación, con sus 2-3 opciones.
 *
 * El icono por tipo de respuesta (✓ / ◑ / ✗) viene del quiz original: ayuda a
 * escanear el cuestionario de un vistazo, sobre todo en Rainforest Alliance
 * con ~30 preguntas.
 */

import type { CertQuestion } from '../lib/types'

const OPTION_ICON: Record<string, string> = {
  yes: '✓',
  partial: '◑',
  no: '✗',
}

export default function CertQuestionCard({
  question,
  sectionName,
  index,
  total,
  value,
  onAnswer,
}: {
  question: CertQuestion
  sectionName: string
  index: number
  total: number
  value: string | undefined
  onAnswer: (value: string) => void
}) {
  return (
    <div className="card card-pad stack stack-4">
      <div className="row row-between row-wrap">
        <span className="eyebrow">
          {sectionName} · Pregunta {index + 1} de {total}
        </span>
        {question.critical && (
          <span className="badge badge-warn">⚠ Requisito mínimo obligatorio</span>
        )}
      </div>

      <h2 className="display display-sm">{question.text}</h2>

      <div className="stack stack-2" role="radiogroup" aria-label={question.text}>
        {question.options.map((option) => (
          <button
            key={option.value}
            type="button"
            role="radio"
            aria-checked={value === option.value}
            className={`cert-option${value === option.value ? ` selected-${option.value}` : ''}`}
            onClick={() => onAnswer(option.value)}
          >
            <span className="cert-option-icon" aria-hidden="true">
              {OPTION_ICON[option.value] ?? '?'}
            </span>
            <span>{option.label}</span>
          </button>
        ))}
      </div>
    </div>
  )
}
