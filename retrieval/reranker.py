"""
Cross-encoder reranker.

Takes vector-search candidates and re-orders them by query–document relevance.
"""

from __future__ import annotations

from typing import Any

DEFAULT_RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"

_model = None
_model_name: str | None = None


def _load_model(model_name: str = DEFAULT_RERANKER_MODEL):
    global _model, _model_name
    if _model is None or _model_name != model_name:
        from sentence_transformers import CrossEncoder

        _model = CrossEncoder(model_name)
        _model_name = model_name
    return _model


def rerank(
    query: str,
    candidates: list[dict[str, Any]],
    *,
    top_k: int | None = None,
    model_name: str = DEFAULT_RERANKER_MODEL,
) -> list[dict[str, Any]]:
    """
    Rerank candidates with a cross-encoder.

    Each candidate must include a `content` field.
    Adds `rerank_score` and sorts descending by that score.
    """
    if not candidates:
        return []

    model = _load_model(model_name)
    pairs = [(query, c.get("content") or "") for c in candidates]
    scores = model.predict(pairs)

    ranked: list[dict[str, Any]] = []
    for candidate, score in zip(candidates, scores, strict=True):
        item = dict(candidate)
        item["rerank_score"] = float(score)
        ranked.append(item)

    ranked.sort(key=lambda x: x["rerank_score"], reverse=True)
    if top_k is not None:
        ranked = ranked[:top_k]
    return ranked
