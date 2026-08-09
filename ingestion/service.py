"""Core ingestion logic."""

from fastapi import UploadFile, HTTPException

from shared.models import IngestionEnvelope, IngestionMetadata
from shared.constants import SCHEMA_VERSION
from shared.utils import utc_now_iso
from ingestion.connectors import CONNECTORS
from ingestion.utils import get_extension
from processing.utils import document_id_for_filename


async def ingest(file: UploadFile) -> IngestionEnvelope:
    """
    Ingest an uploaded file.

    Detects file type from the extension, runs the matching connector,
    and returns a standard envelope for the next pipeline layer.
    document_id is stable per filename so re-uploads replace prior chunks.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    extension = get_extension(file.filename)

    if extension not in CONNECTORS:
        supported = ", ".join(sorted(CONNECTORS.keys()))
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {extension}. Supported: {supported}",
        )

    file_type, connector = CONNECTORS[extension]
    payload = await connector(file)

    return IngestionEnvelope(
        metadata=IngestionMetadata(
            document_id=document_id_for_filename(file.filename),
            filename=file.filename,
            file_type=file_type,
            extension=extension,
            mime_type=file.content_type,
            ingested_at=utc_now_iso(),
            schema_version=SCHEMA_VERSION,
        ),
        payload=payload,
    )
