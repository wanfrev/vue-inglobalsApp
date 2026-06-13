import json
import uuid
from datetime import datetime, timezone

from openai import OpenAI

from app.config import settings
from app.core.rag import search_legal_context
from app.database import insert_simulation
from app.models.schemas import CriterionResult, DADResult

SYSTEM_PROMPT = """
Eres el motor central del Simulador DAD (Documento de Auditoría Digital).
Tu función es actuar como un filtro de cumplimiento legal y contable para Venezuela.

Debes evaluar la propuesta del usuario contra los 5 criterios de la ecuación DAD:
  DAD = Cs + Cv + CS + GT + NI

Criterios:
- Cs (Ciencias Sociales / Juicio Profesional): Capacidad crítica y ética del auditor. ¿La decisión es éticamente defendible?
- Cv (Contexto Venezolano / Sostenibilidad): Cumplimiento con leyes venezolanas, providencias, ASG/ESG.
- CS (Capital Social / Estructuración): ¿La propuesta cumple con la estructura documental requerida por el tipo de entidad?
- GT (Gestión Tecnológica / IA): ¿El proceso es auditable digitalmente? ¿Genera trazabilidad?
- NI (Normas Internacionales): Cumplimiento con NIA, NIIF S1/S2, VEN-NS 0.

Contexto legal relevante recuperado:
{legal_context}

Tipo de entidad: {entity_type}
Marco normativo seleccionado: {framework}

Regla de oro: si la propuesta viola alguna ley o norma, is_valid DEBE ser false.
Sé estricto y cita los artículos específicos.

Responde ÚNICAMENTE con este JSON, sin texto adicional:
{{
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


def _build_system_prompt(
    prompt: str, entity_type: str, framework: str
) -> str:
    legal_results = search_legal_context(prompt, top_k=5)

    if legal_results:
        context_parts = []
        for i, result in enumerate(legal_results, 1):
            context_parts.append(
                f"[{i}] {result.get('title', 'Sin título')} ({result.get('category', 'N/A')})\n"
                f"    Score: {result.get('score', 0):.3f}\n"
                f"    Texto: {result.get('text', '')[:500]}..."
            )
        legal_context = "\n\n".join(context_parts)
    else:
        legal_context = DEFAULT_CONTEXT

    return SYSTEM_PROMPT.format(
        legal_context=legal_context,
        entity_type=entity_type,
        framework=framework,
    )


def run_simulation(prompt: str, entity_type: str, framework: str) -> dict:
    client = OpenAI(
        api_key=settings.DEEPSEEK_API_KEY,
        base_url=settings.DEEPSEEK_BASE_URL,
    )

    system_prompt = _build_system_prompt(prompt, entity_type, framework)

    response = client.chat.completions.create(
        model=settings.DEEPSEEK_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        temperature=settings.DEEPSEEK_TEMPERATURE,
        max_tokens=settings.DEEPSEEK_MAX_TOKENS,
        response_format={"type": "json_object"},
    )

    response_text = response.choices[0].message.content
    result_data = json.loads(response_text)

    dad_result = DADResult(**result_data)

    expediente_id = f"AUD-{datetime.now(timezone.utc).strftime('%Y')}-{uuid.uuid4().hex[:6].upper()}"
    created_at = datetime.now(timezone.utc).isoformat()

    criteria_map = {
        "Cs": dad_result.criteria.get("Cs"),
        "Cv": dad_result.criteria.get("Cv"),
        "CS": dad_result.criteria.get("CS"),
        "GT": dad_result.criteria.get("GT"),
        "NI": dad_result.criteria.get("NI"),
    }

    simulation_data = {
        "expediente_id": expediente_id,
        "created_at": created_at,
        "entity_type": entity_type,
        "framework": framework,
        "prompt": prompt,
        "result_json": response_text,
        "is_valid": 1 if dad_result.is_valid else 0,
        "criteria_cs": criteria_map["Cs"].status if criteria_map["Cs"] else "idle",
        "criteria_cv": criteria_map["Cv"].status if criteria_map["Cv"] else "idle",
        "criteria_cs_cap": criteria_map["CS"].status if criteria_map["CS"] else "idle",
        "criteria_gt": criteria_map["GT"].status if criteria_map["GT"] else "idle",
        "criteria_ni": criteria_map["NI"].status if criteria_map["NI"] else "idle",
        "compliance_score": dad_result.compliance_score,
        "corrective_action": dad_result.corrective_action,
    }

    insert_simulation(simulation_data)

    return {
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
    }
