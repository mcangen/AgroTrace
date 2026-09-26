"""Motor de puntuacion del diagnostico de certificacion.

Replica exactamente el algoritmo del legacy (`certificaciones.html`, funcion
`showResults()`, lineas 999-1026), verificado linea por linea:

    crit_fails = [id in critical_ids si answers.get(id, "no") == "no"]
    hard_fail  = len(crit_fails) > 0

    score_seccion = round_half_up((yes + partial*0.5) / total_seccion * 100)
    overall_score = round_half_up((total_yes + total_partial*0.5) / total * 100)

    verdict = READY        si not hard_fail and overall_score >= 65
            = ALMOST_READY  si not hard_fail and 40 <= overall_score < 65
            = NOT_READY     en cualquier otro caso (incluye siempre hard_fail=True)

Una pregunta ausente del payload cuenta como "no": en el JS original, el `else`
final de `qs.forEach(...)` atrapa tanto un "no" explicito como una respuesta sin
contestar (linea 1013: `else no++`). Replicarlo aqui es necesario para que el
mismo conjunto de respuestas produzca el mismo puntaje en ambos lados.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from app.models import CertificationVerdict
from app.services.certification_data import CertStandardDef, flat_questions, question_text


def _round_half_up(value: float) -> int:
    """Redondeo half-up, igual a `Math.round` de JS.

    El `round()` nativo de Python usa banker's rounding (half-to-even) y puede
    dar un resultado distinto en casos limite -- ej. 64.5 -> JS da 65, Python
    `round()` puede dar 64 -- justo en el borde de un umbral de verdict.
    """
    return math.floor(value + 0.5)


@dataclass(frozen=True)
class SectionScore:
    id: str
    name: str
    score: int
    yes: int
    partial: int
    no: int


@dataclass(frozen=True)
class CriticalGap:
    id: str
    text: str


@dataclass(frozen=True)
class ScoringResult:
    overall_score: int
    verdict: CertificationVerdict
    section_scores: list[SectionScore]
    critical_gaps: list[CriticalGap]
    total_yes: int
    total_partial: int
    total_questions: int


def score_assessment(
    standard_def: CertStandardDef, answers: dict[str, str]
) -> ScoringResult:
    def effective(question_id: str) -> str:
        return answers.get(question_id, "no")

    # Se itera el cuestionario en su orden natural (no el frozenset critical_ids,
    # cuyo orden de iteracion no es estable entre reinicios del proceso) para que
    # la lista de brechas criticas salga siempre en el mismo orden.
    crit_fails = [
        q.id for q in flat_questions(standard_def) if q.critical and effective(q.id) == "no"
    ]
    hard_fail = len(crit_fails) > 0

    section_scores: list[SectionScore] = []
    total_yes = 0
    total_partial = 0
    total_questions = 0

    for section in standard_def.sections:
        yes = partial = no = 0
        for question in section.questions:
            answer = effective(question.id)
            if answer == "yes":
                yes += 1
            elif answer == "partial":
                partial += 1
            else:
                no += 1
        total = len(section.questions)
        score = _round_half_up(((yes + partial * 0.5) / total) * 100) if total else 0

        section_scores.append(
            SectionScore(id=section.id, name=section.name, score=score, yes=yes, partial=partial, no=no)
        )
        total_yes += yes
        total_partial += partial
        total_questions += total

    overall_score = (
        _round_half_up(((total_yes + total_partial * 0.5) / total_questions) * 100)
        if total_questions
        else 0
    )

    if not hard_fail and overall_score >= 65:
        verdict = CertificationVerdict.READY
    elif not hard_fail and 40 <= overall_score < 65:
        verdict = CertificationVerdict.ALMOST_READY
    else:
        verdict = CertificationVerdict.NOT_READY

    critical_gaps = [
        CriticalGap(id=qid, text=question_text(standard_def, qid)) for qid in crit_fails
    ]

    return ScoringResult(
        overall_score=overall_score,
        verdict=verdict,
        section_scores=section_scores,
        critical_gaps=critical_gaps,
        total_yes=total_yes,
        total_partial=total_partial,
        total_questions=total_questions,
    )
