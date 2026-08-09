"""Vector store FastAPI routes — store only."""

from fastapi import APIRouter

from embeddings.models import EmbeddingResult
from vectorstore.service import upsert

router = APIRouter(prefix="/vectorstore", tags=["vectorstore"])


@router.get("/health")
async def health():
    return {"status": "ok", "layer": "vectorstore"}


@router.post("/upsert")
async def upsert_embeddings(embedded: EmbeddingResult):
    """Persist embedded chunks into Chroma."""
    return await upsert(embedded)
