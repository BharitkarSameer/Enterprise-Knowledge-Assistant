"""
Core chunking logic.

MVP strategy:
  - 1 processed section with blocks → 1 chunk
  - skip empty sections (headings that only have child sections)
  - content = section.to_embed_text() (path + serialized blocks)
  - chunk_id is stable per document + section path (re-index upserts, no dupes)
"""

from __future__ import annotations

from processing.models import ProcessingResult
from processing.utils import stable_id
from chunking.models import Chunk, ChunkingResult


async def chunk(processed: ProcessingResult | dict) -> ChunkingResult:
    """Turn a ProcessingResult into embeddable chunks."""
    if isinstance(processed, dict):
        processed = ProcessingResult.model_validate(processed)

    chunks: list[Chunk] = []
    filename = processed.metadata.filename if processed.metadata else None

    for section in processed.sections:
        if not section.blocks:
            continue

        content = section.to_embed_text()
        if not content.strip():
            continue

        path_key = " > ".join(section.path)
        chunks.append(
            Chunk(
                chunk_id=stable_id(
                    "chk",
                    processed.document_id,
                    path_key,
                    section.heading,
                ),
                document_id=processed.document_id,
                section_id=section.section_id,
                heading=section.heading,
                level=section.level,
                path=list(section.path),
                content=content,
                blocks=section.blocks,
                char_count=len(content),
            )
        )

    return ChunkingResult(
        document_id=processed.document_id,
        title=processed.title,
        filename=filename,
        chunks=chunks,
        chunk_count=len(chunks),
    )
