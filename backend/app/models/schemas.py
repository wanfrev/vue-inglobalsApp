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


class SimulateRequest(BaseModel):
    prompt: str
    entity_type: Literal["publica", "privada", "mixta"] = "publica"
    framework: str = "NIA 230"


class SimulateResponse(BaseModel):
    expediente_id: str
    created_at: str
    is_valid: bool
    summary: str
    criteria: dict[str, CriterionResult]
    corrective_action: str
    compliance_score: int


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
    is_valid: bool
    criteria_cs: str
    criteria_cv: str
    criteria_cs_cap: str
    criteria_gt: str
    criteria_ni: str
    compliance_score: int
    corrective_action: str
