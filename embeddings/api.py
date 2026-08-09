"""Embedding FastAPI routes."""

from fastapi import APIRouter

from chunking.models import ChunkingResult
from embeddings.service import embed_chunks

router = APIRouter(prefix="/embeddings", tags=["embeddings"])


@router.get("/health")
async def health():
    return {"status": "ok", "layer": "embeddings"}


@router.post("")
async def embed_document(chunked: ChunkingResult):
    """Embed chunk contents (does not persist)."""
    result = await embed_chunks(chunked)
    # Avoid dumping giant vectors in API responses by default
    return {
        "document_id": result.document_id,
        "title": result.title,
        "model": result.model,
        "dimensions": result.dimensions,
        "item_count": result.item_count,
        "items": [
            {
                "chunk_id": item.chunk_id,
                "heading": item.heading,
                "path": item.path,
                "embedding_dims": len(item.embedding),
            }
            for item in result.items
        ],
    }
