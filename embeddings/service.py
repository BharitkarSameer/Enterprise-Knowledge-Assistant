"""
Core embedding logic.

Turns chunk text into dense vectors. Does NOT persist anything —
storage belongs in the vectorstore layer.
"""

from __future__ import annotations

import asyncio

from chunking.models import ChunkingResult
from embeddings.models import EmbeddedChunk, EmbeddingResult
from embeddings.providers import get_default_provider
from embeddings.providers.base import EmbeddingProvider


async def embed_texts(
    texts: list[str],
    provider: EmbeddingProvider | None = None,
) -> list[list[float]]:
    """Embed raw strings. Useful for query embedding later."""
    provider = provider or get_default_provider()
    return await asyncio.to_thread(provider.embed, texts)


async def embed_chunks(
    chunked: ChunkingResult | dict,
    provider: EmbeddingProvider | None = None,
) -> EmbeddingResult:
    """
    Embed every chunk's `content` and return vectors alongside metadata.

    No database writes happen here.
    """
    if isinstance(chunked, dict):
        chunked = ChunkingResult.model_validate(chunked)

    provider = provider or get_default_provider()
    texts = [c.content for c in chunked.chunks]
    vectors = await asyncio.to_thread(provider.embed, texts)

    items: list[EmbeddedChunk] = []
    for chunk, vector in zip(chunked.chunks, vectors, strict=True):
        items.append(
            EmbeddedChunk(
                chunk_id=chunk.chunk_id,
                document_id=chunk.document_id,
                section_id=chunk.section_id,
                heading=chunk.heading,
                level=chunk.level,
                path=list(chunk.path),
                content=chunk.content,
                blocks=chunk.blocks,
                embedding=vector,
                char_count=chunk.char_count,
            )
        )

    return EmbeddingResult(
        document_id=chunked.document_id,
        title=chunked.title,
        model=provider.model_name,
        dimensions=provider.dimensions,
        items=items,
        item_count=len(items),
    )


# Backwards-friendly alias if callers expect `embed`
async def embed(texts: list[str]) -> list[list[float]]:
    return await embed_texts(texts)
