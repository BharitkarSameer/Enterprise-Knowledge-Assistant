"""Core processing logic — route by file type into structured IR."""

from __future__ import annotations

from fastapi import HTTPException

from shared.models import IngestionEnvelope
from processing.models import ProcessingResult
from processing.markdown_processor import process_markdown


async def process(envelope: IngestionEnvelope | dict) -> ProcessingResult:
    """
    Take an ingestion envelope and return structured sections + blocks.

    Markdown: headings (≤ ###) become sections with a parent path stack;
    tables/code/lists/paragraphs become typed blocks under those sections.
    """
    if isinstance(envelope, dict):
        envelope = IngestionEnvelope.model_validate(envelope)

    file_type = envelope.metadata.file_type

    if file_type == "markdown":
        title, sections = process_markdown(
            str(envelope.payload),
            fallback_title=envelope.metadata.filename,
        )
        return ProcessingResult(
            document_id=envelope.metadata.document_id,
            title=title,
            file_type=file_type,
            sections=sections,
            metadata=envelope.metadata,
        )

    raise HTTPException(
        status_code=400,
        detail=f"No processor implemented for file type: {file_type}",
    )
