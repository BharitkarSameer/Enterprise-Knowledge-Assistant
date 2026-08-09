"""Common schemas shared across pipeline layers."""

from pydantic import BaseModel, Field
from typing import Any


class IngestionMetadata(BaseModel):
    document_id: str
    filename: str
    file_type: str
    extension: str
    mime_type: str | None = None
    ingested_at: str
    schema_version: str = "1.0"


class IngestionEnvelope(BaseModel):
    """Standard output of the ingestion layer — input to processing."""

    metadata: IngestionMetadata
    payload: Any = Field(description="Raw content for the next pipeline layer")
