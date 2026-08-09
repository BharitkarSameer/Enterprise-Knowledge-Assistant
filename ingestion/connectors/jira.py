"""Jira connector — placeholder."""

from fastapi import HTTPException


async def fetch_jira(config: dict):
    raise HTTPException(status_code=501, detail="Jira connector not implemented yet")
