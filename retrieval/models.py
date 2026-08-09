"""Retrieval-layer models."""

from __future__ import annotations

from pydantic import BaseModel, Field


class RetrievedChunk(BaseModel):
    chunk_id: str
    document_id: str
    section_id: str
    heading: str
    level: int
    path: list[str]
    content: str
    vector_score: float = Field(description="Similarity from vector search")
    rerank_score: float | None = Field(
        default=None,
        description="Cross-encoder score after reranking",
    )


class RetrievalResult(BaseModel):
    query: str
    chunks: list[RetrievedChunk]
    candidate_count: int
    returned_count: int
    reranked: bool = True
