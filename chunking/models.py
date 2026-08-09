"""Chunking-layer models — embeddable units derived from processed sections."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from processing.models import Block


class Chunk(BaseModel):
    """One retrieval unit — typically one processed section."""

    chunk_id: str
    document_id: str
    section_id: str
    heading: str
    level: int
    path: list[str] = Field(
        description="Breadcrumb for citations, e.g. Guide > Rollback"
    )
    content: str = Field(description="Text used for embedding")
    blocks: list[Block] = Field(
        default_factory=list,
        description="Structured blocks preserved for UI / generation",
    )
    char_count: int = 0


class ChunkingResult(BaseModel):
    """Output of the chunking layer — input to embeddings."""

    document_id: str
    title: str | None = None
    chunks: list[Chunk]
    chunk_count: int = 0
