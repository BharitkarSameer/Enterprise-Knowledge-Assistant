"""Confluence connector — placeholder."""

from fastapi import HTTPException


async def fetch_confluence(config: dict):
    raise HTTPException(status_code=501, detail="Confluence connector not implemented yet")
