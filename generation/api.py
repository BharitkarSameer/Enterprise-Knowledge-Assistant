"""Generation FastAPI routes — placeholder."""

from fastapi import APIRouter

router = APIRouter(prefix="/generate", tags=["generation"])


@router.get("/health")
async def health():
    return {"status": "ok", "layer": "generation"}
