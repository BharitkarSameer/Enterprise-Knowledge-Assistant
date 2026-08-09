"""Embeddings-layer models."""

from __future__ import annotations

from pydantic import BaseModel, Field

from processing.models import Block


class EmbeddedChunk(BaseModel):
    """A chunk plus its embedding vector."""

    chunk_id: str
    document_id: str
    section_id: str
    heading: str
    level: int
    path: list[str]
    content: str
    blocks: list[Block] = Field(default_factory=list)
    embedding: list[float]
    char_count: int = 0


class EmbeddingResult(BaseModel):
    """Output of the embeddings layer — input to vectorstore."""

    document_id: str
    title: str | None = None
    model: str
    dimensions: int
    items: list[EmbeddedChunk]
    item_count: int = 0
