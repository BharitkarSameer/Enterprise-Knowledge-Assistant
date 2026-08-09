"""Vectorstore models."""

from __future__ import annotations

from pydantic import BaseModel, Field


class UpsertResult(BaseModel):
    document_id: str
    collection: str
    upserted: int
    persist_dir: str


class SearchHit(BaseModel):
    """Raw similarity hit from Chroma (pre-rerank)."""

    chunk_id: str
    document_id: str
    section_id: str
    heading: str
    level: int
    path: list[str]
    content: str
    score: float = Field(description="Vector similarity (higher is better)")
    distance: float = Field(description="Raw Chroma distance (lower is better)")
