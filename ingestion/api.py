"""Ingestion FastAPI routes."""

from fastapi import APIRouter, UploadFile, File

from ingestion.service import ingest

router = APIRouter(prefix="/ingest", tags=["ingestion"])


@router.post("/file")
async def ingest_file(file: UploadFile = File(...)):
    """Upload a file and receive metadata + payload for the next layer."""
    return await ingest(file)
