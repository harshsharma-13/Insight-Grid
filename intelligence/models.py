from __future__ import annotations

from pydantic import BaseModel, Field


class Metric(BaseModel):
    label: str
    value: str | int | float
    detail: str


class ScoreBreakdown(BaseModel):
    overall: float = Field(ge=0, le=100)
    sentiment: float = Field(ge=0, le=100)
    aspect_fit: float = Field(ge=0, le=100)
    complaint_safety: float = Field(ge=0, le=100)
    evidence: float = Field(ge=0, le=100)


class HealthResponse(BaseModel):
    status: str
    service: str
    database: str


class FinderResult(BaseModel):
    phone_id: str
    phone_name: str
    brand: str
    score: ScoreBreakdown
    reason: str
    evidence_label: str
