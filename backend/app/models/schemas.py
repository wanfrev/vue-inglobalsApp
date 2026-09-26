import unicodedata
from typing import Any, Literal

from pydantic import BaseModel, field_validator, model_validator


class _LenientModel(BaseModel):
    """Los LLM a veces devuelven `null` en un campo opcional en vez de omitirlo.
    Se descartan esas claves para que apliquen los valores por defecto, en vez
    de fallar la validación y gastar un reintento (que cuesta tokens/energía)."""

    @model_validator(mode="before")
    @classmethod
    def _drop_nulls(cls, data: Any) -> Any:
        if isinstance(data, dict):
            return {k: v for k, v in data.items() if v is not None}
        return data


class SourceUsed(BaseModel):
    title: str
    category: str
    framework: str = ""
    score: float = 0.0


# ---------------------------------------------------------------------------
# Prompt 1 / Loop 1 — Filtro filosófico, técnico y epistemológico
# ---------------------------------------------------------------------------

class VerifiedClaim(_LenientModel):
    claim: str
    source: str = ""


class DiscardedClaim(_LenientModel):
    claim: str
    reason: str = ""


class Loop1Result(_LenientModel):
    """Salida del Loop 1 del protocolo AOPCCPS+IA: la consulta cruda pasa por
    los tres enfoques (ontológico, fenomenológico, falsabilidad 3/3) contra la
    bibliografía documentada, y queda un borrador lógico solo con lo
    verificado. También infiere tipo de entidad y marco normativo (el usuario
    nunca los elige)."""

    in_scope: bool = True
    out_of_scope_reason: str = ""
    entity_type: Literal["publica", "privada", "mixta"] = "privada"
    framework: str = ""
    ontological: str = ""
    phenomenological: str = ""
    verified_claims: list[VerifiedClaim] = []
    discarded_claims: list[DiscardedClaim] = []
    logical_draft: str = ""
    loop1_passed: bool = True
    missing_info: list[str] = []

    @field_validator("entity_type", mode="before")
    @classmethod
    def _normalize_entity_type(cls, value: Any) -> Any:
        if not isinstance(value, str):
            return "privada"
        plain = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode().strip().lower()
        return plain if plain in ("publica", "privada", "mixta") else "privada"

    @model_validator(mode="after")
    def _draft_required_when_in_scope(self) -> "Loop1Result":
        # Si el modelo dice que la consulta está en alcance pero no entrega
        # borrador, la salida no sirve: falla la validación → reintento.
        if self.in_scope and not self.logical_draft.strip():
            raise ValueError("logical_draft vacío en una consulta dentro de alcance")
        return self


# ---------------------------------------------------------------------------
# Prompt 2 / Loop 2 — Ejecución, eco-eficiencia y freno de mano
# ---------------------------------------------------------------------------

class Loop2Result(_LenientModel):
    final_answer: str
    condition_met: bool = True

    @field_validator("final_answer")
    @classmethod
    def _answer_not_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("final_answer vacío")
        return value


class Loop2Output(Loop2Result):
    """Loop 2 + lo que calcula el servidor sobre la respuesta (no el LLM):
    palabras, y cuánto se podó respecto del borrador lógico del Loop 1."""

    words: int = 0
    draft_words: int = 0
    pruning_ratio: float = 0.0
    max_words: int = 0
    within_word_limit: bool = True


# ---------------------------------------------------------------------------
# Métricas de sostenibilidad por consulta (ODS 12 y 13)
# ---------------------------------------------------------------------------

class UsageInfo(BaseModel):
    """Consumo real de tokens reportado por la API (no estimado por el modelo)
    y su costo asociado, para trazabilidad de sostenibilidad/costo del uso de IA."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0


class LoopMetric(BaseModel):
    name: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0
    energy_wh: float = 0.0


class Sustainability(BaseModel):
    """Tokens y costo son medidos; energía y CO2e son estimaciones a partir de
    los coeficientes de configuración (ver ENERGY_WH_PER_1K_TOKENS)."""

    loops: list[LoopMetric] = []
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0
    cost_per_1k_tokens_usd: float = 0.0
    energy_wh: float = 0.0
    co2_g: float = 0.0
    budget_loop1_tokens: int = 0
    budget_loop2_tokens: int = 0
    budget_total_tokens: int = 0
    energy_wh_per_1k_tokens: float = 0.0
    co2_g_per_kwh: float = 0.0


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

class SimulateRequest(BaseModel):
    prompt: str


class SimulateResponse(BaseModel):
    expediente_id: str = ""
    created_at: str = ""
    in_scope: bool = True
    out_of_scope_reason: str = ""
    entity_type: str = ""
    framework: str = ""
    missing_info: list[str] = []
    sources_used: list[SourceUsed] = []
    loop1: Loop1Result | None = None
    loop2: Loop2Output | None = None
    sustainability: Sustainability | None = None
    usage: UsageInfo = UsageInfo()
    free_queries_used: int = 0
    free_queries_remaining: int = 0
    is_paid: bool = False


class SessionResponse(BaseModel):
    """Respuesta al crear una sesión anónima nueva (sin registro/login)."""

    token: str
    free_queries_used: int
    free_queries_remaining: int
    is_paid: bool


class SessionStatus(BaseModel):
    free_queries_used: int
    free_queries_remaining: int
    is_paid: bool


class DocumentUploadResponse(BaseModel):
    success: bool
    document: dict


class DocumentRecord(BaseModel):
    id: str
    title: str
    category: str
    chunks: int
    indexed_at: str


class SimulationRecord(BaseModel):
    id: int
    expediente_id: str
    created_at: str
    entity_type: str
    framework: str
    prompt: str
    structured_prompt: str = ""
    result_json: str | None = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0
    energy_wh: float = 0.0
    co2_g: float = 0.0
