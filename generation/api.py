"""Generation FastAPI routes."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from generation.service import ask, generate
from retrieval.models import RetrievedChunk

router = APIRouter(tags=["generation"])


class GenerateRequest(BaseModel):
    query: str = Field(min_length=1)
    context: list[RetrievedChunk]
    model: str | None = None


class AskRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int = Field(default=2, ge=1, le=20)
    candidate_k: int = Field(default=6, ge=1, le=50)
    use_reranker: bool = True
    model: str | None = None


@router.get("/generate/health")
async def health():
    from generation.quota import quota_status

    return {"status": "ok", "layer": "generation", "quota": quota_status()}


@router.post("/generate")
async def generate_answer(request: GenerateRequest):
    """Generate an answer from an explicit context package."""
    return await generate(
        request.query,
        request.context,
        model_name=request.model,
    )


@router.post("/ask")
async def ask_question(request: AskRequest):
    """
    Full Q&A path: retrieve (+ rerank) → Gemini answer + citations.
    """
    return await ask(
        request.query,
        top_k=request.top_k,
        candidate_k=request.candidate_k,
        use_reranker=request.use_reranker,
        model_name=request.model,
    )
