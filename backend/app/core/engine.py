import json
import uuid
from datetime import datetime, timezone

from openai import OpenAI

from app.config import settings
from app.core.rag import search_legal_context
from app.database import insert_simulation
from app.models.schemas import DADResult, StructuringResult, UsageInfo

# ---------------------------------------------------------------------------
# Prompt 1 — Organizador
#
# Recibe la pregunta cruda del usuario + los fragmentos legales recuperados
# por RAG (search_legal_context) + lo que el usuario haya adjuntado a ESTA
# consulta puntual (evidencia, no se suma a la base de leyes), y la reformula
# de forma técnica, anclada en esas fuentes. También infiere por su cuenta el
# tipo de entidad y el marco normativo aplicable — el usuario nunca los elige
# manualmente, todo eso vive "detrás" del chat. No emite ningún veredicto de
# cumplimiento todavía: solo estructura y señala qué falta para poder
# responder bien.
# ---------------------------------------------------------------------------

PROMPT_1_SYSTEM = """
Eres el Módulo Organizador del Simulador DAD (Documento de Auditoría Digital).
Tu única función es tomar la consulta cruda de un usuario (auditor, contador
o responsable de cumplimiento en Venezuela) y reformularla de forma técnica y
precisa, ANCLADA en los fragmentos legales/normativos recuperados abajo y en
los documentos que el usuario haya adjuntado a esta consulta. No evalúas
cumplimiento ni das un veredicto: solo organizas la pregunta.

Fragmentos legales/normativos recuperados (RAG):
{legal_context}

Documentos adjuntados por el usuario a esta consulta (evidencia puntual, NO
son leyes — úsalos como contexto de lo que el usuario está preguntando):
{attached_context}

El usuario NO indica tipo de entidad ni marco normativo: debes inferirlos tú
mismo a partir de la consulta, los documentos adjuntos y el contexto legal
recuperado.

Instrucciones:
1. Reescribe la consulta como una pregunta técnica precisa, citando la norma
   o ley específica cuando el fragmento recuperado lo permita (ej. "VEN-NIF 8
   Art. X", "NIA 230 párr. Y"). No inventes artículos que no estén en los
   fragmentos ni en tu conocimiento general confiable.
2. Infiere "entity_type": "publica", "privada" o "mixta". Si la consulta y los
   adjuntos no dan pistas claras, usa "privada" como supuesto por defecto y
   dilo en "missing_info".
3. Infiere "framework": la norma o marco normativo más relevante para esta
   consulta específica (ej. "NIA 230", "VEN-NIF 8", "NIIF S1/S2"), no una
   lista genérica.
4. Lista solo las fuentes de "sources_used" que realmente aplican a esta
   consulta (pueden ser menos de las 5 recuperadas si algunas no son
   relevantes). Si ninguna aplica, deja la lista vacía.
5. Si a la consulta le falta información necesaria para evaluarla con rigor
   (ej. período fiscal, monto, o tuviste que asumir el tipo de entidad),
   inclúyelo en "missing_info". Si no falta nada, deja la lista vacía.

Responde ÚNICAMENTE con este JSON, sin texto adicional:
{{
  "structured_prompt": "Consulta reformulada de forma técnica y anclada en las fuentes",
  "entity_type": "publica|privada|mixta",
  "framework": "Norma o marco normativo más relevante para esta consulta",
  "sources_used": [
    {{"title": "Título de la fuente", "category": "venezolana|internacional|sostenibilidad", "framework": "Ej. VEN-NIF 8", "score": 0.0}}
  ],
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

# Tope de caracteres de texto extraído por archivo adjunto que se manda al
# modelo. No es un límite técnico sino de costo: un PDF completo puede tener
# cientos de miles de caracteres y dispararía el gasto en tokens de una sola
# pregunta. Ver DEEPSEEK_PRICE_*_PER_1M en config.py.
MAX_CHARS_PER_ATTACHMENT = 6000


def _format_attached_context(attachments: list[dict]) -> str:
    if not attachments:
        return "Ninguno."

    parts = []
    for att in attachments:
        text = (att.get("text") or "").strip()
        if not text:
            parts.append(f"[Archivo: {att['name']}] (sin texto extraíble)")
            continue
        truncated = text[:MAX_CHARS_PER_ATTACHMENT]
        if len(text) > MAX_CHARS_PER_ATTACHMENT:
            truncated += "\n[... texto truncado por límite de tamaño ...]"
        parts.append(f"[Archivo: {att['name']}]\n{truncated}")
    return "\n\n".join(parts)


def _format_legal_context(legal_results: list[dict]) -> str:
    if not legal_results:
        return DEFAULT_CONTEXT

    context_parts = []
    for i, result in enumerate(legal_results, 1):
        context_parts.append(
            f"[{i}] {result.get('title', 'Sin título')} ({result.get('category', 'N/A')})\n"
            f"    Score: {result.get('score', 0):.3f}\n"
            f"    Texto: {result.get('text', '')[:500]}..."
        )
    return "\n\n".join(context_parts)


def _get_client() -> OpenAI:
    return OpenAI(
        api_key=settings.DEEPSEEK_API_KEY,
        base_url=settings.DEEPSEEK_BASE_URL,
    )


def _estimate_cost(prompt_tokens: int, completion_tokens: int) -> float:
    input_cost = (prompt_tokens / 1_000_000) * settings.DEEPSEEK_PRICE_INPUT_PER_1M
    output_cost = (completion_tokens / 1_000_000) * settings.DEEPSEEK_PRICE_OUTPUT_PER_1M
    return round(input_cost + output_cost, 6)


def _call_deepseek(client: OpenAI, system_prompt: str, user_prompt: str) -> tuple[dict, UsageInfo]:
    """Llama a DeepSeek y devuelve (json_parseado, uso_de_tokens). El uso de
    tokens viene del campo `usage` de la respuesta de la API, no de algo que
    el modelo reporte dentro de su propio texto."""
    response = client.chat.completions.create(
        model=settings.DEEPSEEK_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=settings.DEEPSEEK_TEMPERATURE,
        max_tokens=settings.DEEPSEEK_MAX_TOKENS,
        response_format={"type": "json_object"},
    )

    data = json.loads(response.choices[0].message.content)

    usage = response.usage
    prompt_tokens = usage.prompt_tokens if usage else 0
    completion_tokens = usage.completion_tokens if usage else 0
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


def _run_structuring_prompt(
    client: OpenAI, raw_prompt: str, attachments: list[dict]
) -> tuple[StructuringResult, str, UsageInfo]:
    """Prompt 1: organiza la consulta a partir del contexto legal recuperado
    y de los archivos que el usuario adjuntó a esta pregunta puntual, e
    infiere tipo de entidad / marco normativo (el usuario no los elige)."""
    legal_results = search_legal_context(raw_prompt, top_k=5)
    legal_context = _format_legal_context(legal_results)
    attached_context = _format_attached_context(attachments)

    system_prompt = PROMPT_1_SYSTEM.format(
        legal_context=legal_context,
        attached_context=attached_context,
    )

    data, usage = _call_deepseek(client, system_prompt, raw_prompt)
    structuring = StructuringResult(**data)
    return structuring, legal_context, usage


def _run_validation_prompt(
    client: OpenAI,
    structuring: StructuringResult,
    legal_context: str,
) -> tuple[DADResult, UsageInfo]:
    """Prompt 2: valida si la pregunta (ya organizada) está bien formulada y
    produce el veredicto DAD, usando el tipo de entidad/marco que ya infirió
    el Prompt 1."""
    sources_text = (
        "\n".join(
            f"- {s.title} ({s.category}"
            + (f", {s.framework}" if s.framework else "")
            + ")"
            for s in structuring.sources_used
        )
        or "Ninguna fuente específica identificada por el organizador."
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
    return dad_result, usage


def run_simulation(prompt: str, attachments: list[dict] | None = None) -> dict:
    """attachments: lista de {"name": str, "text": str} ya extraídos por la
    capa API (ver app/api/simulate.py). Son evidencia de ESTA consulta
    puntual: se usan como contexto para responderla y quedan asociados al
    expediente en el historial, pero NO se indexan en la base de leyes
    compartida (esa se administra aparte, vía /api/v1/documents)."""
    client = _get_client()
    attachments = attachments or []

    structuring, legal_context, usage_1 = _run_structuring_prompt(client, prompt, attachments)
    dad_result, usage_2 = _run_validation_prompt(client, structuring, legal_context)
    total_usage = _sum_usage(usage_1, usage_2)

    expediente_id = f"AUD-{datetime.now(timezone.utc).strftime('%Y')}-{uuid.uuid4().hex[:6].upper()}"
    created_at = datetime.now(timezone.utc).isoformat()

    criteria_map = {k: dad_result.criteria.get(k) for k in ("Cs", "Cv", "CS", "GT", "NI")}
    attached_names = [a["name"] for a in attachments]

    result_payload = {
        "expediente_id": expediente_id,
        "created_at": created_at,
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
        "sources_used": [s.model_dump() for s in structuring.sources_used],
        "missing_info": structuring.missing_info,
        "attached_files": attached_names,
        "question_well_formed": dad_result.question_well_formed,
        "question_feedback": dad_result.question_feedback,
        "usage": total_usage.model_dump(),
    }

    simulation_data = {
        "expediente_id": expediente_id,
        "created_at": created_at,
        "entity_type": structuring.entity_type,
        "framework": structuring.framework,
        "prompt": prompt,
        "structured_prompt": structuring.structured_prompt,
        "attached_files": json.dumps(attached_names, ensure_ascii=False),
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
