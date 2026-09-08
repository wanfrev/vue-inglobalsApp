from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class CriterionResult(BaseModel):
    status: Literal["passed", "failed"]
    detail: str
    article_ref: str = ""


class DADResult(BaseModel):
    is_valid: bool
    summary: str
    criteria: dict[str, CriterionResult]
    corrective_action: str
    compliance_score: int = Field(ge=0, le=100)
    question_well_formed: bool = True
    question_feedback: str = ""


class SourceUsed(BaseModel):
    title: str
    category: str
    framework: str = ""
    score: float = 0.0


class StructuringResult(BaseModel):
    """Salida del Prompt 1 (organizador): la pregunta reformulada y anclada
    en las fuentes legales recuperadas por RAG y en los adjuntos de esta
    consulta, más el tipo de entidad/marco normativo que infirió por su
    cuenta (el usuario nunca los elige), y lo que falte por aclarar."""

    structured_prompt: str
    entity_type: Literal["publica", "privada", "mixta"] = "privada"
    framework: str = ""
    sources_used: list[SourceUsed] = []
    missing_info: list[str] = []


class UsageInfo(BaseModel):
    """Consumo real de tokens reportado por la API (no estimado por el modelo)
    y su costo asociado, para trazabilidad de sostenibilidad/costo del uso de IA."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0


class SimulateResponse(BaseModel):
    expediente_id: str
    created_at: str
    is_valid: bool
    summary: str
    criteria: dict[str, CriterionResult]
    corrective_action: str
    compliance_score: int
    structured_prompt: str = ""
    entity_type: str = ""
    framework: str = ""
    sources_used: list[SourceUsed] = []
    missing_info: list[str] = []
    attached_files: list[str] = []
    question_well_formed: bool = True
    question_feedback: str = ""
    usage: UsageInfo = UsageInfo()


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
    attached_files: list[str] = []
    is_valid: bool
    criteria_cs: str
    criteria_cv: str
    criteria_cs_cap: str
    criteria_gt: str
    criteria_ni: str
    compliance_score: int
    corrective_action: str
    question_well_formed: bool = True
    question_feedback: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0
