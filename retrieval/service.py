"""
Core retrieval logic.

1. Embed the query
2. Vector search in Chroma (broad candidate set)
3. Cross-encoder rerank → final top_k chunks
"""

from __future__ import annotations

import asyncio

from embeddings.service import embed_texts
from retrieval.models import RetrievedChunk, RetrievalResult
from retrieval.reranker import rerank
from vectorstore.service import search as vector_search


async def retrieve(
    query: str,
    *,
    top_k: int = 5,
    candidate_k: int = 15,
    document_id: str | None = None,
    use_reranker: bool = True,
) -> RetrievalResult:
    """
    Retrieve the most relevant chunks for a natural-language query.

    `candidate_k` is how many vector hits to pull before reranking.
    `top_k` is how many chunks to return after reranking.
    """
    query = (query or "").strip()
    if not query:
        raise ValueError("Query must not be empty")

    if candidate_k < top_k:
        candidate_k = top_k

    query_vector = (await embed_texts([query]))[0]
    hits = await vector_search(
        query_vector,
        top_k=candidate_k,
        document_id=document_id,
    )

    candidates = [
        {
            "chunk_id": hit.chunk_id,
            "document_id": hit.document_id,
            "section_id": hit.section_id,
            "heading": hit.heading,
            "level": hit.level,
            "path": list(hit.path),
            "content": hit.content,
            "vector_score": hit.score,
        }
        for hit in hits
    ]

    if use_reranker and candidates:
        ranked = await asyncio.to_thread(
            rerank,
            query,
            candidates,
            top_k=top_k,
        )
        reranked = True
    else:
        ranked = candidates[:top_k]
        for item in ranked:
            item["rerank_score"] = None
        reranked = False

    chunks = [
        RetrievedChunk(
            chunk_id=item["chunk_id"],
            document_id=item["document_id"],
            section_id=item["section_id"],
            heading=item["heading"],
            level=item["level"],
            path=item["path"],
            content=item["content"],
            vector_score=float(item["vector_score"]),
            rerank_score=(
                None
                if item.get("rerank_score") is None
                else float(item["rerank_score"])
            ),
        )
        for item in ranked
    ]

    return RetrievalResult(
        query=query,
        chunks=chunks,
        candidate_count=len(candidates),
        returned_count=len(chunks),
        reranked=reranked,
    )
