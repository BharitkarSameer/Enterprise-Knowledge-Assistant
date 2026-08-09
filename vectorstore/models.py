"""Vectorstore models."""

from __future__ import annotations

from pydantic import BaseModel


class UpsertResult(BaseModel):
    document_id: str
    collection: str
    upserted: int
    persist_dir: str
