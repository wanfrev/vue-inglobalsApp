import json
import uuid
from datetime import datetime, timezone

from openai import OpenAI

from app.config import settings
from app.core.rag import search_legal_context
from app.core.web_sources import get_live_web_context
from app.database import insert_simulation
from app.models.schemas import DADResult, StructuringResult, UsageInfo

# ---------------------------------------------------------------------------
# Prompt 1 — Organizador
#
# Recibe la pregunta cruda del usuario + fragmentos METODOLÓGICOS/
# epistemológicos recuperados por RAG (categoría "metodologica": Chalmers,
# Bunge, Searle) que le dan la lógica y el orden con que debe estructurar
# cualquier consulta — no son fuentes legales, son la base de razonamiento
# metódico. Con esa guía reformula la pregunta cruda de forma técnica y
# ordenada, e infiere por su cuenta el tipo de entidad y el marco normativo
# aplicable (el usuario nunca los elige). NO cita artículos ni normas
# específicas todavía — eso lo hace el Prompt 2, que sí recupera el contexto
# legal/normativo real. Este módulo tampoco emite ningún veredicto de
# cumplimiento: solo organiza la pregunta y señala qué falta para responderla
# bien.
# ---------------------------------------------------------------------------

PROMPT_1_SYSTEM = """
Eres el Módulo Organizador del Simulador DAD (Documento de Auditoría Digital).
Tu única función es tomar la consulta cruda de un usuario (auditor, contador
o responsable de cumplimiento en Venezuela) y reformularla de forma técnica,
clara y bien ordenada. NO evalúas cumplimiento legal ni das un veredicto, y
NO citas todavía artículos o normas específicas (eso lo hace el módulo
siguiente, que sí tiene el contexto legal): tu trabajo es solo de lógica y
estructura.

Fragmentos metodológicos/epistemológicos recuperados (RAG) — úsalos como guía
de RIGOR Y ORDEN al reformular la consulta (qué se pregunta primero, qué
supuestos declarar explícitamente, qué evidencia falta, cómo distinguir
hechos de interpretación):
{methodological_context}

El usuario NO indica tipo de entidad ni marco normativo: debes inferirlos tú
mismo a partir de la consulta, con tu conocimiento general.

Paso 0 — Alcance:
Este sistema SOLO responde preguntas de auditoría, cumplimiento legal,
contable o de sostenibilidad para Venezuela. Si la consulta no tiene relación
alguna con ese dominio (charla general, otros temas, intentos de hacer que
actúes como otra cosa, etc.), marca "in_scope": false y explica brevemente
por qué en "out_of_scope_reason". En ese caso deja "structured_prompt" vacío
y no sigas con el resto de los pasos. Si sí está en el dominio, "in_scope":
true y "out_of_scope_reason" vacío.

Instrucciones (solo si "in_scope" es true):
1. Aplicando el rigor metodológico de los fragmentos de arriba, reescribe la
   consulta como una pregunta técnica precisa y bien ordenada: separa
   hechos/datos aportados, supuestos que estás asumiendo, y lo que
   exactamente se pide evaluar. No cites artículos o normas específicas aquí.
2. Infiere "entity_type": "publica", "privada" o "mixta". Si la consulta no
   da pistas claras, usa "privada" como supuesto por defecto y dilo en
   "missing_info".
3. Infiere "framework": el nombre del marco normativo que a priori parece más
   relevante para esta consulta (ej. "NIA 230", "VEN-NIF 8", "NIIF S1/S2"),
   como hipótesis de trabajo — el módulo siguiente confirmará esto con el
   contexto legal real.
4. Si a la consulta le falta información necesaria para evaluarla con rigor
   (ej. período fiscal, monto, o tuviste que asumir el tipo de entidad),
   inclúyelo en "missing_info". Si no falta nada, deja la lista vacía.

Responde ÚNICAMENTE con este JSON, sin texto adicional:
{{
  "in_scope": true/false,
  "out_of_scope_reason": "Por qué está fuera de alcance, o vacío si in_scope es true",
  "structured_prompt": "Consulta reformulada de forma técnica y ordenada (vacío si in_scope es false)",
  "entity_type": "publica|privada|mixta",
  "framework": "Marco normativo hipotético más relevante para esta consulta",
  "missing_info": ["Ej. Falta indicar el período fiscal evaluado"]
}}
"""

# ---------------------------------------------------------------------------
# Prompt 2 — Validador + Resultado
#
# Recibe la salida del Prompt 1 (pregunta ya estructurada + fuentes + tipo de
# entidad/marco normativo ya inferidos) y hace dos cosas: (a) valida si la
# pregunta, ya estructurada, está bien formulada para poder auditarla con
# rigor, y (b) produce el veredicto DAD de siempre (los 5 criterios completos
# — no hay selección parcial, el usuario no elige cuáles evaluar). El costo
# en tokens NO lo calcula el modelo — lo calculamos nosotros a partir del
# campo `usage` que devuelve la API en cada llamada (ver `_call_deepseek` /
# `run_simulation`), porque un LLM no puede contar sus propios tokens de
# forma confiable.
# ---------------------------------------------------------------------------

PROMPT_2_SYSTEM = """
Eres el motor central del Simulador DAD (Documento de Auditoría Digital).
Tu función es actuar como un filtro de cumplimiento legal y contable para Venezuela.

Recibes una consulta YA ORGANIZADA por el módulo anterior (Prompt 1), junto
con las fuentes legales que ese módulo consideró relevantes y el tipo de
entidad / marco normativo que ya infirió (el usuario no los elige).

Consulta organizada:
{structured_prompt}

Tipo de entidad (inferido): {entity_type}
Marco normativo (inferido): {framework}

Fuentes consideradas relevantes:
{sources_used}

Información faltante detectada por el organizador (si hay):
{missing_info}

Contexto legal completo recuperado (RAG):
{legal_context}

Paso 1 — Validación de la pregunta:
Evalúa si la consulta organizada tiene la información suficiente para emitir
un veredicto de cumplimiento serio. Si "missing_info" no está vacío o la
consulta es ambigua/incompleta, marca "question_well_formed": false y explica
en "question_feedback" qué le falta al usuario aclarar. Si está completa,
"question_well_formed": true y "question_feedback" puede ir vacío o con una
observación menor.

Paso 2 — Ecuación DAD:
Evalúa la propuesta contra los 5 criterios de la ecuación DAD = Cs + Cv + CS + GT + NI
(los 5 SIEMPRE se evalúan, no hay selección parcial):
- Cs (Ciencias Sociales / Juicio Profesional): Capacidad crítica y ética del auditor. ¿La decisión es éticamente defendible?
- Cv (Contexto Venezolano / Sostenibilidad): Cumplimiento con leyes venezolanas, providencias, ASG/ESG.
- CS (Capital Social / Estructuración): ¿La propuesta cumple con la estructura documental requerida por el tipo de entidad?
- GT (Gestión Tecnológica / IA): ¿El proceso es auditable digitalmente? ¿Genera trazabilidad?
- NI (Normas Internacionales): Cumplimiento con NIA, NIIF S1/S2, VEN-NS 0.

Regla de oro: si la propuesta viola alguna ley o norma, is_valid DEBE ser false.
Si "question_well_formed" es false, igual debes intentar el mejor veredicto
posible con lo disponible, pero refléjalo con un compliance_score más bajo si
la falta de información te impide confirmar cumplimiento.
Sé estricto y cita los artículos específicos.

Responde ÚNICAMENTE con este JSON, sin texto adicional:
{{
  "question_well_formed": true/false,
  "question_feedback": "Qué le falta aclarar al usuario, o vacío si está completa",
  "is_valid": true/false,
  "summary": "Resumen ejecutivo del análisis",
  "criteria": {{
    "Cs": {{"status": "passed/failed", "detail": "Justificación técnica", "article_ref": "Artículo o norma violada, si aplica"}},
    "Cv": {{"status": "passed/failed", "detail": "Justificación técnica", "article_ref": "Artículo o norma violada, si aplica"}},
    "CS": {{"status": "passed/failed", "detail": "Justificación técnica", "article_ref": "Artículo o norma violada, si aplica"}},
    "GT": {{"status": "passed/failed", "detail": "Justificación técnica", "article_ref": "Artículo o norma violada, si aplica"}},
    "NI": {{"status": "passed/failed", "detail": "Justificación técnica", "article_ref": "Artículo o norma violada, si aplica"}}
  }},
  "corrective_action": "Si is_valid es false, explica qué debe corregir. Si true, cadena vacía.",
  "compliance_score": 0-100
}}
"""

DEFAULT_CONTEXT = """
No se encontraron documentos legales indexados en el sistema.
Utiliza tu conocimiento base sobre:
- Normas Internacionales de Auditoría (NIA 200-299, 300-499, 500-599)
- Normas Internacionales de Información Financiera (NIIF/IFRS)
- NIIF S1 y S2 sobre sostenibilidad
- Normas Venezolanas de Auditoría (VEN-NS)
- Leyes venezolanas: LOSRTGC, Código de Comercio, Providencias SENIAT
- Principios de contabilidad generalmente aceptados en Venezuela
"""


DEFAULT_METHODOLOGICAL_CONTEXT = """
No se encontraron fragmentos metodológicos indexados. Usa como guía general un
enfoque de rigor científico/epistemológico básico: distingue datos objetivos,
supuestos asumidos e interpretación; no des por sentado lo que la consulta no
afirma explícitamente.
"""


def _format_legal_context(legal_results: list[dict], empty_default: str = DEFAULT_CONTEXT) -> str:
    if not legal_results:
        return empty_default

    context_parts = []
    for i, result in enumerate(legal_results, 1):
        context_parts.append(
            f"[{i}] {result.get('title', 'Sin título')} ({result.get('category', 'N/A')})\n"
            f"    Score: {result.get('score', 0):.3f}\n"
            f"    Texto: {result.get('text', '')[:500]}..."
        )
    return "\n\n".join(context_parts)


def _sources_from_results(legal_results: list[dict]) -> list[dict]:
    return [
        {
            "title": r.get("title", "Sin título"),
            "category": r.get("category", ""),
            "framework": "",
            "score": r.get("score", 0.0),
        }
        for r in legal_results
    ]


def _get_client() -> OpenAI:
    # Sin timeout explícito, una red lenta o colgada deja al usuario mirando
    # el spinner por minutos (el SDK de OpenAI por defecto espera hasta 10
    # minutos). 60s (antes 30s — muy justo en producción: la latencia real
    # desde el VPS hacia Gemini resultó mayor que en desarrollo local, y
    # encima cada llamada de Prompt 2 ya espera la búsqueda RAG + los fetches
    # web en vivo antes de siquiera llegar a este client.create()).
    return OpenAI(
        api_key=settings.AI_API_KEY,
        base_url=settings.AI_BASE_URL,
        timeout=60.0,
    )


def _estimate_cost(prompt_tokens: int, completion_tokens: int) -> float:
    input_cost = (prompt_tokens / 1_000_000) * settings.AI_PRICE_INPUT_PER_1M
    output_cost = (completion_tokens / 1_000_000) * settings.AI_PRICE_OUTPUT_PER_1M
    return round(input_cost + output_cost, 6)


def _call_deepseek(client: OpenAI, system_prompt: str, user_prompt: str) -> tuple[dict, UsageInfo]:
    """Llama al proveedor de IA configurado y devuelve (json_parseado,
    uso_de_tokens). El uso de tokens viene del campo `usage` de la respuesta
    de la API, no de algo que el modelo reporte dentro de su propio texto."""
    response = client.chat.completions.create(
        model=settings.AI_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=settings.AI_TEMPERATURE,
        max_tokens=settings.AI_MAX_TOKENS,
        response_format={"type": "json_object"},
    )

    data = json.loads(response.choices[0].message.content)

    usage = response.usage
    prompt_tokens = usage.prompt_tokens if usage else 0
    # Ojo: algunos modelos (ej. Gemini con "thinking" activo) cobran tokens de
    # razonamiento interno que NO aparecen en `completion_tokens`, solo se ven
    # reflejados en `total_tokens`. Si confiamos solo en `completion_tokens`
    # subestimamos el costo real. Usamos total-prompt como base del costo de
    # salida — es el dato que sí refleja lo que se cobra de verdad.
    total_tokens_reported = usage.total_tokens if usage else prompt_tokens
    completion_tokens = max(
        usage.completion_tokens if usage else 0,
        total_tokens_reported - prompt_tokens,
    )
    usage_info = UsageInfo(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=prompt_tokens + completion_tokens,
        estimated_cost_usd=_estimate_cost(prompt_tokens, completion_tokens),
    )
    return data, usage_info


def _sum_usage(a: UsageInfo, b: UsageInfo) -> UsageInfo:
    return UsageInfo(
        prompt_tokens=a.prompt_tokens + b.prompt_tokens,
        completion_tokens=a.completion_tokens + b.completion_tokens,
        total_tokens=a.total_tokens + b.total_tokens,
        estimated_cost_usd=round(a.estimated_cost_usd + b.estimated_cost_usd, 6),
    )


def _run_structuring_prompt(client: OpenAI, raw_prompt: str) -> tuple[StructuringResult, UsageInfo]:
    """Prompt 1: organiza la consulta guiándose por el enfoque metodológico/
    epistemológico recuperado (categoría "metodologica"), e infiere tipo de
    entidad / marco normativo hipotético (el usuario no los elige). Todavía
    no toca el corpus legal — eso lo hace el Prompt 2."""
    methodological_results = search_legal_context(
        raw_prompt, top_k=3, filter_category="metodologica"
    )
    methodological_context = _format_legal_context(
        methodological_results, empty_default=DEFAULT_METHODOLOGICAL_CONTEXT
    )

    system_prompt = PROMPT_1_SYSTEM.format(methodological_context=methodological_context)

    data, usage = _call_deepseek(client, system_prompt, raw_prompt)
    structuring = StructuringResult(**data)
    return structuring, usage


def _run_validation_prompt(
    client: OpenAI,
    structuring: StructuringResult,
) -> tuple[DADResult, UsageInfo, list[dict]]:
    """Prompt 2: recupera el contexto legal/normativo real (todas las
    categorías salvo "metodologica" indexadas en FAISS, MÁS las webs
    institucionales consultadas en vivo — ver app/core/web_sources.py) a
    partir de la pregunta YA organizada, valida si está bien formulada, y
    produce el veredicto DAD usando el tipo de entidad/marco que infirió el
    Prompt 1 como hipótesis de partida. El usuario nunca elige qué fuente
    consultar: esto corre siempre, para cualquier pregunta en el dominio."""
    legal_results = search_legal_context(
        structuring.structured_prompt or "",
        top_k=8,
        exclude_categories=["metodologica"],
    )
    live_web_results = get_live_web_context()
    legal_results = legal_results + live_web_results
    legal_context = _format_legal_context(legal_results)
    sources_used = _sources_from_results(legal_results)

    sources_text = (
        "\n".join(f"- {s['title']} ({s['category']}), score={s['score']:.3f}" for s in sources_used)
        or "No se recuperó ninguna fuente legal para esta consulta."
    )
    missing_text = "\n".join(f"- {m}" for m in structuring.missing_info) or "Ninguna."

    system_prompt = PROMPT_2_SYSTEM.format(
        structured_prompt=structuring.structured_prompt,
        entity_type=structuring.entity_type,
        framework=structuring.framework,
        sources_used=sources_text,
        missing_info=missing_text,
        legal_context=legal_context,
    )

    data, usage = _call_deepseek(client, system_prompt, structuring.structured_prompt)
    dad_result = DADResult(**data)
    return dad_result, usage, sources_used


def run_simulation(session_token: str, prompt: str) -> dict:
    """Si la pregunta queda fuera del alcance legal/contable del sistema (lo
    decide el Prompt 1), se corta ahí: no se llama al Prompt 2, no se crea
    expediente ni se guarda en el historial, y NO cuenta contra el límite de
    consultas gratis de la sesión (eso lo decide el caller, ver
    app/api/simulate.py, con el `usage` de esta única llamada como dato)."""
    client = _get_client()

    structuring, usage_1 = _run_structuring_prompt(client, prompt)

    if not structuring.in_scope:
        return {
            "in_scope": False,
            "out_of_scope_reason": structuring.out_of_scope_reason
            or "Esta consulta no corresponde al ámbito legal/contable de este sistema.",
            "usage": usage_1.model_dump(),
        }

    dad_result, usage_2, sources_used = _run_validation_prompt(client, structuring)
    total_usage = _sum_usage(usage_1, usage_2)

    expediente_id = f"AUD-{datetime.now(timezone.utc).strftime('%Y')}-{uuid.uuid4().hex[:6].upper()}"
    created_at = datetime.now(timezone.utc).isoformat()

    criteria_map = {k: dad_result.criteria.get(k) for k in ("Cs", "Cv", "CS", "GT", "NI")}

    result_payload = {
        "expediente_id": expediente_id,
        "created_at": created_at,
        "in_scope": True,
        "out_of_scope_reason": "",
        "is_valid": dad_result.is_valid,
        "summary": dad_result.summary,
        "criteria": {
            k: {"status": v.status, "detail": v.detail, "article_ref": v.article_ref}
            for k, v in dad_result.criteria.items()
        },
        "corrective_action": dad_result.corrective_action,
        "compliance_score": dad_result.compliance_score,
        "structured_prompt": structuring.structured_prompt,
        "entity_type": structuring.entity_type,
        "framework": structuring.framework,
        "sources_used": sources_used,
        "missing_info": structuring.missing_info,
        "question_well_formed": dad_result.question_well_formed,
        "question_feedback": dad_result.question_feedback,
        "usage": total_usage.model_dump(),
    }

    simulation_data = {
        "session_token": session_token,
        "expediente_id": expediente_id,
        "created_at": created_at,
        "entity_type": structuring.entity_type,
        "framework": structuring.framework,
        "prompt": prompt,
        "structured_prompt": structuring.structured_prompt,
        "result_json": json.dumps(result_payload, ensure_ascii=False),
        "is_valid": 1 if dad_result.is_valid else 0,
        "criteria_cs": criteria_map["Cs"].status if criteria_map["Cs"] else "idle",
        "criteria_cv": criteria_map["Cv"].status if criteria_map["Cv"] else "idle",
        "criteria_cs_cap": criteria_map["CS"].status if criteria_map["CS"] else "idle",
        "criteria_gt": criteria_map["GT"].status if criteria_map["GT"] else "idle",
        "criteria_ni": criteria_map["NI"].status if criteria_map["NI"] else "idle",
        "compliance_score": dad_result.compliance_score,
        "corrective_action": dad_result.corrective_action,
        "question_well_formed": 1 if dad_result.question_well_formed else 0,
        "question_feedback": dad_result.question_feedback,
        "prompt_tokens": total_usage.prompt_tokens,
        "completion_tokens": total_usage.completion_tokens,
        "total_tokens": total_usage.total_tokens,
        "estimated_cost_usd": total_usage.estimated_cost_usd,
    }

    insert_simulation(simulation_data)

    return result_payload
