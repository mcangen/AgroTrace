"""Catalogo de preguntas de certificacion: Fairtrade y Rainforest Alliance.

Contenido portado literalmente (ids, textos de preguntas/opciones y hojas de ruta)
desde `legacy/src/main/resources/static/certificaciones.html`, lineas 663-881
(objeto `CERT_DATA` del quiz original de la hackaton). No se alteraron textos ni
ids al portarlo -- son los mismos que ya se probaron con productores reales.

El campo `failIds` del objeto original no se porto: es codigo muerto, confirmado
que nunca se lee en ningun calculo del legacy (`showResults()`), solo `criticalIds`
importa para determinar el fallo critico.

Esta es la fuente unica de verdad del catalogo -- el frontend no lo duplica, lo
consume via `GET /certification/standards` (ver `app.schemas.certification` y
`app.api.routes.certification`). El motor de puntuacion (`certification_scoring.py`)
tambien lee de aqui, así que un id de pregunta nunca puede divergir entre lo que
el usuario responde y lo que el backend evalua.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.models import CertificationStandard


@dataclass(frozen=True)
class CertOption:
    value: str  # 'yes' | 'partial' | 'no'
    label: str


@dataclass(frozen=True)
class CertQuestion:
    id: str
    text: str
    critical: bool
    options: tuple[CertOption, ...]


@dataclass(frozen=True)
class CertSection:
    id: str
    name: str
    questions: tuple[CertQuestion, ...]


@dataclass(frozen=True)
class RoadmapStage:
    etapa: str
    title: str
    type: str  # 'active' | 'warn' | 'done'
    tasks: tuple[str, ...]


@dataclass(frozen=True)
class CertStandardDef:
    key: CertificationStandard
    name: str
    badge: str
    color: str
    critical_ids: frozenset[str]
    sections: tuple[CertSection, ...]
    fallback_roadmap: tuple[RoadmapStage, ...]


def _q(id: str, text: str, critical: bool, *opts: tuple[str, str]) -> CertQuestion:
    return CertQuestion(
        id=id,
        text=text,
        critical=critical,
        options=tuple(CertOption(value=v, label=lbl) for v, lbl in opts),
    )


# --- Fairtrade --------------------------------------------------------------

_FAIRTRADE_SECTIONS = (
    CertSection(
        id="A",
        name="Organización y estructura",
        questions=(
            _q(
                "A1",
                "¿Su organización es una cooperativa, asociación u otra forma de "
                "organización colectiva de pequeños productores?",
                True,
                ("yes", "Sí, somos una organización colectiva"),
                ("partial", "Estoy tramitando la formalización"),
                ("no", "No, somos una finca individual"),
            ),
            _q(
                "A2",
                "¿Tienen al menos 10 productores miembros activos?",
                True,
                ("yes", "Sí, 10 o más productores"),
                ("no", "No, menos de 10 productores"),
            ),
            _q(
                "A3",
                "¿Tienen estatutos o reglamento interno aprobado y un órgano de "
                "gobierno electo?",
                True,
                ("yes", "Sí, estatutos y gobernanza en regla"),
                ("partial", "En proceso de formalización"),
                ("no", "No tenemos todavía"),
            ),
            _q(
                "A4",
                "¿Llevan actas o registros de sus asambleas y decisiones internas?",
                False,
                ("yes", "Sí, tenemos registros actualizados"),
                ("no", "No llevamos actas formales"),
            ),
        ),
    ),
    CertSection(
        id="B",
        name="Producto y mercado",
        questions=(
            _q(
                "B1",
                "¿Tienen identificado al menos un producto para certificar bajo "
                "Fairtrade?",
                True,
                ("yes", "Sí, tenemos producto definido"),
                ("no", "Aún no hemos definido el producto"),
            ),
            _q(
                "B2",
                "¿Conocen el volumen aproximado de producción anual?",
                False,
                ("yes", "Sí, conocemos nuestros volúmenes"),
                ("no", "No tenemos este dato"),
            ),
            _q(
                "B3",
                "¿Tienen clientes interesados o que exijan la certificación "
                "Fairtrade?",
                False,
                ("yes", "Sí, ya tenemos compradores interesados"),
                ("partial", "No aún, pero estamos buscando"),
                ("no", "No tenemos contactos de mercado"),
            ),
        ),
    ),
    CertSection(
        id="C",
        name="Prácticas laborales y sociales",
        questions=(
            _q(
                "C1",
                "¿La producción se basa principalmente en mano de obra familiar?",
                False,
                ("yes", "Sí, trabajo familiar mayoritariamente"),
                ("no", "No, principalmente mano de obra contratada"),
            ),
            _q(
                "C2",
                "¿Existe algún mecanismo para proteger la salud y seguridad de "
                "los trabajadores?",
                False,
                ("yes", "Sí, tenemos mecanismos documentados"),
                ("partial", "Tenemos prácticas pero sin documentar"),
                ("no", "No tenemos nada formal"),
            ),
            _q(
                "C3",
                "¿Está prohibido el trabajo infantil en las fincas y tienen "
                "alguna forma de verificarlo?",
                True,
                ("yes", "Sí, prohibido y con mecanismos de verificación"),
                ("partial", "Está prohibido pero sin verificación formal"),
                ("no", "No tenemos esta política"),
            ),
            _q(
                "C4",
                "¿Tienen alguna política o práctica de no discriminación dentro "
                "de la organización?",
                False,
                ("yes", "Sí, política explícita de no discriminación"),
                ("no", "No tenemos esta política"),
            ),
        ),
    ),
    CertSection(
        id="D",
        name="Prácticas ambientales",
        questions=(
            _q(
                "D1",
                "¿Aplican buenas prácticas agrícolas o manejo integrado de "
                "plagas?",
                False,
                ("yes", "Sí, documentadas y aplicadas"),
                ("partial", "Las aplicamos pero sin documentar"),
                ("no", "No tenemos estas prácticas"),
            ),
            _q(
                "D2",
                "¿Han recibido asistencia técnica o capacitación ambiental en "
                "los últimos 2 años?",
                False,
                ("yes", "Sí, hemos recibido capacitación reciente"),
                ("no", "No hemos recibido asistencia técnica"),
            ),
            _q(
                "D3",
                "¿Conocen la lista de plaguicidas prohibidos por Fairtrade y "
                "evitan su uso?",
                True,
                ("yes", "Sí, la conocemos y cumplimos"),
                ("partial", "La conocemos parcialmente"),
                ("no", "No la conocemos"),
            ),
        ),
    ),
    CertSection(
        id="E",
        name="Finanzas y gestión",
        questions=(
            _q(
                "E1",
                "¿Llevan contabilidad básica de ingresos y gastos de la "
                "organización?",
                True,
                ("yes", "Sí, contabilidad básica al día"),
                ("no", "No llevamos registros financieros"),
            ),
            _q(
                "E2",
                "¿Han administrado alguna vez un fondo colectivo (prima "
                "Fairtrade u otro fondo social)?",
                False,
                ("yes", "Sí, tenemos experiencia con fondos colectivos"),
                ("no", "No hemos manejado fondos colectivos"),
            ),
            _q(
                "E3",
                "¿Han realizado alguna auditoría interna o externa de sus "
                "finanzas en los últimos 3 años?",
                False,
                ("yes", "Sí, tenemos auditoría reciente"),
                ("no", "No hemos tenido auditorías"),
            ),
        ),
    ),
    CertSection(
        id="F",
        name="Conocimiento Fairtrade",
        questions=(
            _q(
                "F1",
                "¿Conocen los requisitos generales del Estándar Fairtrade para "
                "Organizaciones de Pequeños Productores (SPO)?",
                False,
                ("yes", "Sí, conocemos el estándar en detalle"),
                ("partial", "Tenemos conocimiento básico"),
                ("no", "No lo conocemos"),
            ),
            _q(
                "F2",
                "¿Han contactado ya a una certificadora acreditada por "
                "Fairtrade International (como FLOCERT)?",
                False,
                ("yes", "Sí, ya estamos en contacto"),
                ("no", "No hemos contactado aún"),
            ),
            _q(
                "F3",
                "¿Tienen presupuesto o acceso a financiamiento para cubrir los "
                "costos de la auditoría y certificación?",
                False,
                ("yes", "Sí, tenemos presupuesto disponible"),
                ("partial", "Estamos gestionando financiamiento"),
                ("no", "No tenemos presupuesto aún"),
            ),
        ),
    ),
)

_FAIRTRADE_ROADMAP = (
    RoadmapStage(
        etapa="Etapa 1 · 1-2 meses",
        title="Documentación y gobernanza",
        type="active",
        tasks=(
            "Revisar y actualizar estatutos alineados al Estándar SPO",
            "Actualizar actas de asamblea y lista de miembros",
            "Formalizar por escrito la política de no trabajo infantil y no "
            "discriminación",
            "Actualizar organigrama y datos del comité directivo",
        ),
    ),
    RoadmapStage(
        etapa="Etapa 2 · 1 mes",
        title="Formación interna sobre el Estándar Fairtrade",
        type="active",
        tasks=(
            "Descargar y estudiar el Estándar Fairtrade para SPO en "
            "fairtrade.net",
            "Identificar requisitos obligatorios (shall) vs. de desarrollo "
            "progresivo",
            "Realizar al menos una sesión informativa con los socios",
        ),
    ),
    RoadmapStage(
        etapa="Etapa 3 · Preparación previa",
        title="Gestión de la Prima Fairtrade",
        type="warn",
        tasks=(
            "Establecer el comité de la Prima (mínimo 3 personas, con "
            "representación de género)",
            "Diseñar o actualizar el reglamento de uso de la prima",
            "Documentar proyectos anteriores del fondo social si los hubiera",
        ),
    ),
    RoadmapStage(
        etapa="Etapa 4 · Paralelo a anteriores",
        title="Buenas prácticas ambientales y laborales",
        type="warn",
        tasks=(
            "Inventariar insumos y verificar que ninguno esté en la lista de "
            "plaguicidas prohibidos",
            "Registrar prácticas de manejo ambiental existentes",
            "Documentar acciones de salud y seguridad para los trabajadores",
        ),
    ),
    RoadmapStage(
        etapa="Etapa 5 · Tras completar 1-4",
        title="Contacto con FLOCERT y solicitud oficial",
        type="done",
        tasks=(
            "Registrarse en flocert.net y solicitar cotización",
            "Preparar el expediente: lista de miembros, estados financieros, "
            "mapa de fincas",
            "Coordinar la fecha de auditoría inicial",
        ),
    ),
    RoadmapStage(
        etapa="Etapa 6 · Antes de la auditoría",
        title="Simulacro interno",
        type="done",
        tasks=(
            "Realizar autoevaluación interna usando la lista de verificación "
            "del Estándar SPO",
            "Corregir hallazgos internos antes de la visita del auditor",
        ),
    ),
)

_FAIRTRADE = CertStandardDef(
    key=CertificationStandard.FAIRTRADE,
    name="Fairtrade",
    badge="🌿",
    color="#1db954",
    critical_ids=frozenset({"A1", "A2", "A3", "B1", "C3", "D3", "E1"}),
    sections=_FAIRTRADE_SECTIONS,
    fallback_roadmap=_FAIRTRADE_ROADMAP,
)


# --- Rainforest Alliance -----------------------------------------------------

_RA_SECTIONS = (
    CertSection(
        id="S1",
        name="Información general y legal",
        questions=(
            _q(
                "S1Q1",
                "¿La organización o finca está legalmente registrada y "
                "autorizada para operar?",
                True,
                ("yes", "Sí, estamos legalmente registrados"),
                ("partial", "En proceso de registro"),
                ("no", "No, no estamos registrados"),
            ),
            _q(
                "S1Q2",
                "¿Posees documentos que demuestren propiedad, arriendo o uso "
                "legal de la tierra?",
                True,
                ("yes", "Sí, tenemos documentos legales de la tierra"),
                ("no", "No tenemos documentación legal de la tierra"),
            ),
            _q(
                "S1Q3",
                "¿La operación cumple con la legislación laboral, ambiental y "
                "comercial aplicable?",
                True,
                ("yes", "Sí, cumplimos con toda la legislación"),
                ("partial", "Cumplimos parcialmente"),
                ("no", "No cumplimos con algunos requisitos legales"),
            ),
            _q(
                "S1Q4",
                "¿La organización está registrada o preparada para registrarse "
                "en la plataforma Rainforest Alliance?",
                False,
                ("yes", "Sí, ya estamos registrados"),
                ("partial", "En proceso"),
                ("no", "No conocemos la plataforma aún"),
            ),
        ),
    ),
    CertSection(
        id="S2",
        name="Gestión y administración",
        questions=(
            _q(
                "S2Q1",
                "¿Existe un plan de manejo o gestión documentado y actualizado?",
                False,
                ("yes", "Sí, plan documentado y vigente"),
                ("partial", "Existe pero desactualizado"),
                ("no", "No tenemos plan de manejo"),
            ),
            _q(
                "S2Q2",
                "¿Se realizan evaluaciones de riesgo periódicas sobre aspectos "
                "ambientales, sociales y laborales?",
                False,
                ("yes", "Sí, evaluaciones periódicas"),
                ("no", "No realizamos evaluaciones de riesgo"),
            ),
            _q(
                "S2Q3",
                "¿La organización cuenta con un mecanismo para recibir y "
                "gestionar quejas o denuncias?",
                False,
                ("yes", "Sí, contamos con este mecanismo"),
                ("no", "No tenemos mecanismo de quejas"),
            ),
        ),
    ),
    CertSection(
        id="S3",
        name="Geolocalización y mapeo",
        questions=(
            _q(
                "S3Q1",
                "¿La operación cuenta con mapas actualizados de las áreas "
                "productivas?",
                False,
                ("yes", "Sí, mapas actualizados disponibles"),
                ("no", "No tenemos mapas de las áreas"),
            ),
            _q(
                "S3Q2",
                "¿Se dispone de coordenadas GPS de las unidades de producción?",
                False,
                ("yes", "Sí, tenemos coordenadas GPS"),
                ("no", "No tenemos coordenadas GPS"),
            ),
            _q(
                "S3Q3",
                "¿Los mapas identifican cuerpos de agua, ecosistemas y áreas "
                "protegidas?",
                False,
                ("yes", "Sí, incluyen esta información"),
                ("no", "No, los mapas no incluyen esta info"),
            ),
        ),
    ),
    CertSection(
        id="S4",
        name="Buenas prácticas agrícolas",
        questions=(
            _q(
                "S4Q1",
                "¿Se utilizan únicamente agroquímicos autorizados legalmente?",
                False,
                ("yes", "Sí, solo productos autorizados"),
                ("no", "No siempre se verifica la autorización"),
            ),
            _q(
                "S4Q2",
                "¿Existe una estrategia documentada de Manejo Integrado de "
                "Plagas?",
                False,
                ("yes", "Sí, estrategia documentada"),
                ("partial", "Tenemos prácticas pero sin documentar"),
                ("no", "No tenemos estrategia de MIP"),
            ),
            _q(
                "S4Q3",
                "¿Los aplicadores reciben capacitación periódica sobre manejo "
                "seguro de agroquímicos?",
                False,
                ("yes", "Sí, capacitación periódica"),
                ("no", "No hay capacitación en esto"),
            ),
            _q(
                "S4Q4",
                "¿Las aplicaciones de agroquímicos quedan registradas "
                "documentalmente?",
                False,
                ("yes", "Sí, todos los registros al día"),
                ("no", "No llevamos registros de aplicaciones"),
            ),
            _q(
                "S4Q5",
                "¿Se implementan prácticas de conservación de suelo y agua?",
                False,
                ("yes", "Sí, prácticas activas de conservación"),
                ("partial", "Algunas prácticas informales"),
                ("no", "No tenemos estas prácticas"),
            ),
        ),
    ),
    CertSection(
        id="S5",
        name="Cumplimiento social y laboral",
        questions=(
            _q(
                "S5Q1",
                "¿Puedes confirmar que NO existe trabajo infantil en la "
                "operación?",
                True,
                ("yes", "Sí, confirmo que no existe trabajo infantil"),
                ("no", "No puedo confirmar esto"),
            ),
            _q(
                "S5Q2",
                "¿Puedes confirmar que NO existe trabajo forzoso?",
                True,
                ("yes", "Sí, confirmo que no existe trabajo forzoso"),
                ("no", "No puedo confirmar esto"),
            ),
            _q(
                "S5Q3",
                "¿Los trabajadores reciben al menos el salario mínimo legal?",
                True,
                ("yes", "Sí, se paga salario mínimo o más"),
                ("no", "No siempre se cumple el mínimo"),
            ),
            _q(
                "S5Q4",
                "¿Existe una política contra discriminación, acoso y violencia "
                "laboral?",
                False,
                ("yes", "Sí, política documentada"),
                ("partial", "Prácticas informales"),
                ("no", "No tenemos esta política"),
            ),
            _q(
                "S5Q5",
                "¿Los trabajadores tienen acceso a agua potable y servicios "
                "sanitarios?",
                False,
                ("yes", "Sí, acceso garantizado"),
                ("no", "No siempre está disponible"),
            ),
        ),
    ),
    CertSection(
        id="S6",
        name="Medio ambiente",
        questions=(
            _q(
                "S6Q1",
                "¿Puedes confirmar que NO ha existido deforestación relacionada "
                "con la operación después de las fechas límite de Rainforest "
                "Alliance?",
                True,
                ("yes", "Sí, confirmo que no ha habido deforestación"),
                ("no", "No puedo confirmar esto o ha existido deforestación"),
            ),
            _q(
                "S6Q2",
                "¿La operación evita producir dentro de áreas protegidas o "
                "ecosistemas restringidos?",
                False,
                ("yes", "Sí, no producimos en áreas protegidas"),
                ("no", "No siempre se verifica esto"),
            ),
            _q(
                "S6Q3",
                "¿Se protegen ríos, quebradas y cuerpos de agua mediante zonas "
                "de amortiguamiento?",
                False,
                ("yes", "Sí, zonas de protección establecidas"),
                ("partial", "Algunas prácticas informales"),
                ("no", "No tenemos zonas de amortiguamiento"),
            ),
            _q(
                "S6Q4",
                "¿Los residuos sólidos y peligrosos se manejan adecuadamente?",
                False,
                ("yes", "Sí, manejo adecuado documentado"),
                ("partial", "Manejo básico sin documentar"),
                ("no", "No tenemos manejo estructurado"),
            ),
        ),
    ),
    CertSection(
        id="S7",
        name="Trazabilidad",
        questions=(
            _q(
                "S7Q1",
                "¿La organización puede identificar el origen de todo el "
                "producto certificado?",
                True,
                ("yes", "Sí, trazabilidad completa"),
                ("partial", "Trazabilidad parcial"),
                ("no", "No tenemos capacidad de trazabilidad"),
            ),
            _q(
                "S7Q2",
                "¿Existe separación entre producto certificado y no "
                "certificado?",
                False,
                ("yes", "Sí, separación clara y documentada"),
                ("no", "No hay separación formal"),
            ),
            _q(
                "S7Q3",
                "¿Se registran compras, ventas, producción y movimientos del "
                "producto?",
                False,
                ("yes", "Sí, todos los movimientos registrados"),
                ("no", "No llevamos estos registros"),
            ),
        ),
    ),
    CertSection(
        id="S8",
        name="Capacitación y mejora continua",
        questions=(
            _q(
                "S8Q1",
                "¿La organización realiza capacitaciones periódicas sobre "
                "sostenibilidad y seguridad?",
                False,
                ("yes", "Sí, programa de capacitación activo"),
                ("partial", "Capacitaciones ocasionales"),
                ("no", "No realizamos capacitaciones"),
            ),
            _q(
                "S8Q2",
                "¿Se implementan acciones correctivas cuando se detectan "
                "incumplimientos?",
                False,
                ("yes", "Sí, proceso formal de corrección"),
                ("no", "No tenemos proceso de mejora continua"),
            ),
            _q(
                "S8Q3",
                "¿Existe disposición para recibir auditorías y mejorar "
                "continuamente?",
                False,
                ("yes", "Sí, estamos comprometidos con la mejora"),
                ("no", "No estamos seguros de esto"),
            ),
        ),
    ),
)

_RA_ROADMAP = (
    RoadmapStage(
        etapa="Paso 1 · Inmediato",
        title="Registro legal y documentación de la tierra",
        type="active",
        tasks=(
            "Formalizar el registro legal de la organización o finca",
            "Obtener y organizar documentos de propiedad, arriendo o uso legal",
            "Verificar cumplimiento de legislación laboral y ambiental",
        ),
    ),
    RoadmapStage(
        etapa="Paso 2 · 1-2 meses",
        title="Plan de manejo y gestión documental",
        type="active",
        tasks=(
            "Desarrollar o actualizar el plan de manejo documentado",
            "Establecer mecanismo de quejas y denuncias",
            "Asignar responsable de sostenibilidad y cumplimiento",
            "Implementar evaluaciones de riesgo periódicas",
        ),
    ),
    RoadmapStage(
        etapa="Paso 3 · 1 mes",
        title="Mapeo y geolocalización",
        type="warn",
        tasks=(
            "Levantar mapas actualizados de las áreas productivas",
            "Registrar coordenadas GPS de todas las unidades de producción",
            "Identificar en los mapas: cuerpos de agua, ecosistemas y áreas "
            "protegidas",
        ),
    ),
    RoadmapStage(
        etapa="Paso 4 · Paralelo",
        title="Buenas prácticas agrícolas",
        type="warn",
        tasks=(
            "Documentar estrategia de Manejo Integrado de Plagas",
            "Capacitar aplicadores en manejo seguro de agroquímicos",
            "Establecer registros documentales de todas las aplicaciones",
            "Implementar prácticas de conservación de suelo y agua",
        ),
    ),
    RoadmapStage(
        etapa="Paso 5 · Antes de la auditoría",
        title="Trazabilidad y controles de producto",
        type="active",
        tasks=(
            "Implementar sistema de trazabilidad completo desde el origen",
            "Establecer separación física entre producto certificado y no "
            "certificado",
            "Registrar compras, ventas, producción y movimientos del producto",
        ),
    ),
    RoadmapStage(
        etapa="Paso 6 · Solicitud oficial",
        title="Registro en plataforma y auditoría",
        type="done",
        tasks=(
            "Registrarse en la plataforma oficial de Rainforest Alliance",
            "Preparar expediente completo para la auditoría",
            "Contratar auditor certificado y coordinar fecha de visita",
        ),
    ),
)

_RAINFOREST_ALLIANCE = CertStandardDef(
    key=CertificationStandard.RAINFOREST_ALLIANCE,
    name="Rainforest Alliance",
    badge="☀️",
    color="#f5a623",
    critical_ids=frozenset(
        {"S1Q1", "S1Q2", "S1Q3", "S5Q1", "S5Q2", "S5Q3", "S6Q1", "S7Q1"}
    ),
    sections=_RA_SECTIONS,
    fallback_roadmap=_RA_ROADMAP,
)


CERT_STANDARDS: dict[CertificationStandard, CertStandardDef] = {
    CertificationStandard.FAIRTRADE: _FAIRTRADE,
    CertificationStandard.RAINFOREST_ALLIANCE: _RAINFOREST_ALLIANCE,
}


def flat_questions(standard_def: CertStandardDef) -> list[CertQuestion]:
    """Todas las preguntas del estandar en una sola lista, sin agrupar por seccion."""
    return [q for section in standard_def.sections for q in section.questions]


def question_text(standard_def: CertStandardDef, question_id: str) -> str:
    """Texto de una pregunta por id; usado para resolver los criticos fallidos."""
    for question in flat_questions(standard_def):
        if question.id == question_id:
            return question.text
    return question_id
