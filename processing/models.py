"""Processing-layer models — structured document IR for chunking."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from shared.models import IngestionMetadata

BlockType = Literal["paragraph", "list", "table", "code", "subheading"]


class TableContent(BaseModel):
    headers: list[str]
    rows: list[list[str]]


class CodeContent(BaseModel):
    language: str | None = None
    code: str


class Block(BaseModel):
    block_id: str
    type: BlockType
    content: Any = Field(
        description="Shape depends on type: str | list[str] | TableContent | CodeContent"
    )


class Section(BaseModel):
    """One chunkable unit: a heading (level ≤ max) and its blocks."""

    section_id: str
    heading: str
    level: int
    path: list[str] = Field(
        description="Breadcrumb from root heading down to this section"
    )
    blocks: list[Block] = Field(default_factory=list)

    def to_embed_text(self) -> str:
        """Serialize section for embedding / later chunking."""
        lines: list[str] = []
        if self.path:
            lines.append("Section: " + " > ".join(self.path))
            lines.append("")

        for block in self.blocks:
            if block.type == "paragraph":
                lines.append(str(block.content))
                lines.append("")
            elif block.type == "subheading":
                lines.append(str(block.content))
                lines.append("")
            elif block.type == "list":
                items = block.content if isinstance(block.content, list) else []
                for item in items:
                    lines.append(f"- {item}")
                lines.append("")
            elif block.type == "table":
                table = (
                    block.content
                    if isinstance(block.content, dict)
                    else block.content.model_dump()
                )
                headers = table.get("headers", [])
                rows = table.get("rows", [])
                if headers:
                    lines.append(" | ".join(str(h) for h in headers))
                    lines.append(" | ".join("---" for _ in headers))
                for row in rows:
                    lines.append(" | ".join(str(c) for c in row))
                lines.append("")
            elif block.type == "code":
                code = (
                    block.content
                    if isinstance(block.content, dict)
                    else block.content.model_dump()
                )
                lang = code.get("language") or ""
                lines.append(f"```{lang}".rstrip())
                lines.append(code.get("code", ""))
                lines.append("```")
                lines.append("")

        return "\n".join(lines).strip()


class ProcessingResult(BaseModel):
    """Output of the processing layer — input to chunking."""

    document_id: str
    title: str | None = None
    file_type: str
    sections: list[Section]
    metadata: IngestionMetadata
