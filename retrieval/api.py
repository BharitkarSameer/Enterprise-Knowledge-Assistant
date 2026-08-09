"""Retrieval FastAPI routes — placeholder."""

from fastapi import APIRouter

router = APIRouter(prefix="/retrieve", tags=["retrieval"])


@router.get("/health")
async def health():
    return {"status": "ok", "layer": "retrieval"}
