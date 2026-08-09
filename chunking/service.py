"""
Core chunking logic.

MVP strategy:
  - 1 processed section with blocks → 1 chunk
  - skip empty sections (headings that only have child sections)
  - content = section.to_embed_text() (path + serialized blocks)
"""

from __future__ import annotations

from processing.models import ProcessingResult
from processing.utils import new_id
from chunking.models import Chunk, ChunkingResult


async def chunk(processed: ProcessingResult | dict) -> ChunkingResult:
    """Turn a ProcessingResult into embeddable chunks."""
    if isinstance(processed, dict):
        processed = ProcessingResult.model_validate(processed)

    chunks: list[Chunk] = []

    for section in processed.sections:
        if not section.blocks:
            continue

        content = section.to_embed_text()
        if not content.strip():
            continue

        chunks.append(
            Chunk(
                chunk_id=new_id("chk"),
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
        chunks=chunks,
        chunk_count=len(chunks),
    )
