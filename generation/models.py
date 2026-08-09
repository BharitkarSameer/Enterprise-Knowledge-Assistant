"""Generation-layer models."""

from __future__ import annotations

from pydantic import BaseModel, Field

from retrieval.models import RetrievedChunk


class Citation(BaseModel):
    path: list[str]
    heading: str
    chunk_id: str


class GenerationResult(BaseModel):
    query: str
    answer: str
    citations: list[Citation] = Field(default_factory=list)
    sources: list[RetrievedChunk] = Field(default_factory=list)
    model: str
