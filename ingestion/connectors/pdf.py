"""PDF connector — placeholder."""

from fastapi import UploadFile, HTTPException


async def parse_pdf(file: UploadFile):
    raise HTTPException(status_code=501, detail="PDF connector not implemented yet")
