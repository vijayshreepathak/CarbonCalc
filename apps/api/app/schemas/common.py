from __future__ import annotations

from pydantic import BaseModel, Field


class TimeWindow(BaseModel):
    from_: str = Field(alias="from")
    to: str


class LineageReference(BaseModel):
    source: str
    source_path: str | None = None
    source_key: str | None = None
    ingested_at: str | None = None


class AssumptionsRecord(BaseModel):
    notes: list[str] = []
    exclusions: list[str] = []

