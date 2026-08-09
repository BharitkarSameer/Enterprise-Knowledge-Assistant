"""
Generation layer — Gemini grounded answers from retrieved chunks.
"""

from __future__ import annotations

import asyncio
import os

from fastapi import HTTPException

from generation.models import Citation, GenerationResult
from generation.prompts import SYSTEM_PROMPT, build_user_prompt
from generation.quota import (
    acquire_gemini_slot,
    mark_daily_exhausted,
    quota_status,
)
from retrieval.models import RetrievedChunk
from retrieval.service import retrieve

# New API keys get 404 on gemini-2.5-flash ("no longer available to new users").
# Override via GEMINI_MODEL in .env if needed.
DEFAULT_MODEL = "gemini-3-flash-preview"

# Keep prompts tiny — free tier is request-count limited (5 RPM / 20 RPD), not TPM.
MAX_CONTEXT_CHARS = 900
DEFAULT_TOP_K = 2
DEFAULT_CANDIDATE_K = 6


def _require_api_key() -> str:
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key or key.startswith("your_gemini"):
        raise HTTPException(
            status_code=500,
            detail="GEMINI_API_KEY is not set. Add it to your .env file.",
        )
    return key


def _is_rate_limit_error(exc: Exception) -> bool:
    lower = str(exc).lower()
    return (
        "resource_exhausted" in lower
        or "exceeded your current quota" in lower
        or "429" in lower
        or "too many requests" in lower
    )


def _looks_like_daily_quota(exc: Exception) -> bool:
    """Google free-tier daily blocks often include limit: 0 / free_tier."""
    lower = str(exc).lower()
    return (
        "limit: 0" in lower
        or "free_tier" in lower
        or "per_day" in lower
        or "perday" in lower
        or "daily" in lower
    )


def _friendly_gemini_error(exc: Exception) -> HTTPException:
    message = str(exc)
    lower = message.lower()
    if "404" in lower or "not_found" in lower or "no longer available" in lower:
        model = os.getenv("GEMINI_MODEL", DEFAULT_MODEL)
        return HTTPException(
            status_code=404,
            detail=(
                f"Gemini model '{model}' was not found for this API key. "
                "New keys often cannot use gemini-2.5-flash; set GEMINI_MODEL to "
                "gemini-3-flash-preview, gemini-3.1-flash-lite, or "
                "gemini-flash-lite-latest."
            ),
        )
    if _is_rate_limit_error(exc):
        status = quota_status()
        return HTTPException(
            status_code=429,
            detail=(
                "Gemini rate limit hit. Free-tier Flash is typically "
                f"{status['rpm_limit']} RPM / {status['rpd_limit']} RPD "
                f"(local day usage {status['rpd_used']}/{status['rpd_limit']}). "
                "Wait ~60s for RPM, or until tomorrow for RPD. "
                "See https://ai.google.dev/gemini-api/docs/rate-limits"
            ),
        )
    if "api key" in lower or "permission" in lower or "unauthenticated" in lower:
        return HTTPException(
            status_code=401,
            detail="Gemini rejected the API key. Check GEMINI_API_KEY in your .env file.",
        )
    # Keep a short provider snippet so UI/logs are actionable.
    snippet = message.replace("\n", " ").strip()
    if len(snippet) > 240:
        snippet = snippet[:240] + "…"
    return HTTPException(
        status_code=502,
        detail=f"Gemini request failed ({exc.__class__.__name__}): {snippet}",
    )


def _call_gemini_once(prompt: str, *, model_name: str, api_key: str) -> str:
    """Single Gemini call using google.genai, with legacy fallback."""
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
            ),
        )
        text = getattr(response, "text", None)
        if not text:
            raise RuntimeError("Gemini returned an empty response")
        return text.strip()
    except ImportError:
        pass
    except Exception as exc:
        if "google.genai" not in str(exc) and "No module named" not in str(exc):
            raise

    import google.generativeai as genai_legacy

    genai_legacy.configure(api_key=api_key)
    model = genai_legacy.GenerativeModel(
        model_name=model_name,
        system_instruction=SYSTEM_PROMPT,
    )
    response = model.generate_content(prompt)
    text = getattr(response, "text", None)
    if not text:
        raise RuntimeError("Gemini returned an empty response")
    return text.strip()


async def _call_gemini(prompt: str, *, model_name: str, api_key: str) -> str:
    """
    Call Gemini once under local RPM/RPD limits.
    At most one RPM-aware retry — never burn the 20/day budget with multi-retries.
    """
    await acquire_gemini_slot()
    try:
        return await asyncio.to_thread(
            _call_gemini_once,
            prompt,
            model_name=model_name,
            api_key=api_key,
        )
    except Exception as first:  # noqa: BLE001
        if not _is_rate_limit_error(first):
            raise
        if _looks_like_daily_quota(first):
            mark_daily_exhausted()
            raise
        # Per-minute: wait one full minute window, then a single retry.
        await asyncio.sleep(13)
        await acquire_gemini_slot()
        try:
            return await asyncio.to_thread(
                _call_gemini_once,
                prompt,
                model_name=model_name,
                api_key=api_key,
            )
        except Exception as second:  # noqa: BLE001
            if _is_rate_limit_error(second) and _looks_like_daily_quota(second):
                mark_daily_exhausted()
            raise


async def generate(
    query: str,
    context: list[RetrievedChunk] | list[dict],
    *,
    model_name: str | None = None,
) -> GenerationResult:
    """Generate an answer from an explicit context list."""
    query = (query or "").strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query must not be empty")

    model_name = model_name or os.getenv("GEMINI_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL
    api_key = _require_api_key()

    normalized: list[dict] = []
    sources: list[RetrievedChunk] = []
    for item in context:
        if isinstance(item, RetrievedChunk):
            sources.append(item)
            normalized.append(item.model_dump())
        else:
            chunk = RetrievedChunk.model_validate(item)
            sources.append(chunk)
            normalized.append(chunk.model_dump())

    compact = [
        {
            "path": item.get("path"),
            "heading": item.get("heading"),
            "content": (item.get("content") or "")[:MAX_CONTEXT_CHARS],
        }
        for item in normalized
    ]
    prompt = build_user_prompt(query, compact)

    try:
        answer = await _call_gemini(
            prompt,
            model_name=model_name,
            api_key=api_key,
        )
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001 - map provider errors to HTTP
        raise _friendly_gemini_error(exc) from None

    citations: list[Citation] = []
    seen_paths: set[str] = set()
    for chunk in sources:
        key = " > ".join(chunk.path) if chunk.path else chunk.heading
        if key in seen_paths:
            continue
        seen_paths.add(key)
        citations.append(
            Citation(
                path=list(chunk.path),
                heading=chunk.heading,
                chunk_id=chunk.chunk_id,
            )
        )

    return GenerationResult(
        query=query,
        answer=answer,
        citations=citations,
        sources=sources,
        model=model_name,
    )


async def ask(
    query: str,
    *,
    top_k: int = DEFAULT_TOP_K,
    candidate_k: int = DEFAULT_CANDIDATE_K,
    use_reranker: bool = True,
    model_name: str | None = None,
) -> GenerationResult:
    """Retrieve relevant chunks, then generate a grounded Gemini answer."""
    retrieval = await retrieve(
        query,
        top_k=top_k,
        candidate_k=candidate_k,
        use_reranker=use_reranker,
    )
    if not retrieval.chunks:
        return GenerationResult(
            query=query,
            answer="I could not find relevant information in the indexed documents.",
            citations=[],
            sources=[],
            model=model_name or os.getenv("GEMINI_MODEL", DEFAULT_MODEL),
        )
    return await generate(
        query,
        retrieval.chunks,
        model_name=model_name,
    )
