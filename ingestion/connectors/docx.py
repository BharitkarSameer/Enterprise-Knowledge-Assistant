"""DOCX connector — placeholder."""

from fastapi import UploadFile, HTTPException


async def parse_docx(file: UploadFile):
    raise HTTPException(status_code=501, detail="DOCX connector not implemented yet")
