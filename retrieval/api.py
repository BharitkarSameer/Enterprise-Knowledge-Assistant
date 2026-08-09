"""Retrieval FastAPI routes."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from retrieval.service import retrieve

router = APIRouter(prefix="/retrieve", tags=["retrieval"])


class RetrieveRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)
    candidate_k: int = Field(default=15, ge=1, le=50)
    document_id: str | None = None
    use_reranker: bool = True


@router.get("/health")
async def health():
    return {"status": "ok", "layer": "retrieval"}


@router.post("")
async def retrieve_chunks(request: RetrieveRequest):
    """
    Embed query → vector search → rerank → return relevant chunks.

    Response includes chunk content (tables/code included) and path for citations.
    """
    return await retrieve(
        request.query,
        top_k=request.top_k,
        candidate_k=request.candidate_k,
        document_id=request.document_id,
        use_reranker=request.use_reranker,
    )
