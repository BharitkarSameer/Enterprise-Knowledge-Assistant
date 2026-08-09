"""
Markdown processor.

Walks raw markdown and builds sections with a heading path stack.

Chunk boundary rule:
  - Headings at level <= MAX_SECTION_LEVEL (default 3 / ###) start a new section
  - Deeper headings are kept as subheading blocks inside the current section

Blocks under a section preserve structure: paragraph, list, table, code.
"""

from __future__ import annotations

from shared.constants import MAX_SECTION_LEVEL
from processing.models import (
    Block,
    CodeContent,
    Section,
    TableContent,
)
from processing.utils import (
    is_fence,
    is_heading,
    is_list_item,
    is_table_separator,
    new_id,
    normalize_markdown,
    split_table_row,
)


def process_markdown(
    content: str,
    *,
    fallback_title: str | None = None,
    max_section_level: int = MAX_SECTION_LEVEL,
) -> tuple[str | None, list[Section]]:
    """
    Parse markdown into (title, sections).

    title: first level-1 heading, else fallback_title / first section heading.
    """
    text = normalize_markdown(content)
    lines = text.split("\n")

    sections: list[Section] = []
    path_stack: list[tuple[int, str]] = []  # (level, heading)
    current: Section | None = None
    title: str | None = None

    def ensure_section() -> Section:
        nonlocal current
        if current is not None:
            return current
        heading = fallback_title or "Introduction"
        path = [heading]
        current = Section(
            section_id=new_id("sec"),
            heading=heading,
            level=1,
            path=path,
            blocks=[],
        )
        sections.append(current)
        path_stack.clear()
        path_stack.append((1, heading))
        return current

    def start_section(level: int, heading: str) -> Section:
        nonlocal current, title
        while path_stack and path_stack[-1][0] >= level:
            path_stack.pop()
        path_stack.append((level, heading))
        path = [h for _, h in path_stack]

        if title is None and level == 1:
            title = heading

        current = Section(
            section_id=new_id("sec"),
            heading=heading,
            level=level,
            path=path,
            blocks=[],
        )
        sections.append(current)
        return current

    def add_block(block: Block) -> None:
        ensure_section().blocks.append(block)

    i = 0
    n = len(lines)

    while i < n:
        line = lines[i]
        stripped = line.strip()

        # Skip blank lines between blocks
        if not stripped:
            i += 1
            continue

        # --- Code fence ---
        fence_match = is_fence(stripped)
        if fence_match:
            fence_char = fence_match.group(1)[0]
            fence_len = len(fence_match.group(1))
            language = fence_match.group(2) or None
            i += 1
            code_lines: list[str] = []
            while i < n:
                close = is_fence(lines[i].strip())
                if (
                    close
                    and close.group(1)[0] == fence_char
                    and len(close.group(1)) >= fence_len
                    and not close.group(2)
                ):
                    i += 1
                    break
                code_lines.append(lines[i])
                i += 1
            add_block(
                Block(
                    block_id=new_id("blk"),
                    type="code",
                    content=CodeContent(
                        language=language,
                        code="\n".join(code_lines),
                    ).model_dump(),
                )
            )
            continue

        # --- Heading ---
        heading_match = is_heading(stripped)
        if heading_match:
            level = len(heading_match.group(1))
            heading_text = heading_match.group(2).strip()
            if level <= max_section_level:
                start_section(level, heading_text)
            else:
                # Fold deeper headings into the current section
                hashes = "#" * level
                add_block(
                    Block(
                        block_id=new_id("blk"),
                        type="subheading",
                        content=f"{hashes} {heading_text}",
                    )
                )
            i += 1
            continue

        # --- Table (header row + separator) ---
        if (
            "|" in stripped
            and i + 1 < n
            and is_table_separator(lines[i + 1].strip())
        ):
            headers = split_table_row(stripped)
            i += 2  # skip header + separator
            rows: list[list[str]] = []
            while i < n and "|" in lines[i] and lines[i].strip():
                if is_table_separator(lines[i].strip()):
                    i += 1
                    continue
                row = split_table_row(lines[i].strip())
                # Pad / trim to header width
                if len(row) < len(headers):
                    row = row + [""] * (len(headers) - len(row))
                elif len(row) > len(headers):
                    row = row[: len(headers)]
                rows.append(row)
                i += 1
            add_block(
                Block(
                    block_id=new_id("blk"),
                    type="table",
                    content=TableContent(headers=headers, rows=rows).model_dump(),
                )
            )
            continue

        # --- List ---
        if is_list_item(line):
            items: list[str] = []
            while i < n:
                raw = lines[i]
                if not raw.strip():
                    # blank line ends list unless next line continues list
                    if i + 1 < n and is_list_item(lines[i + 1]):
                        i += 1
                        continue
                    break
                list_match = is_list_item(raw)
                if not list_match:
                    break
                items.append(list_match.group(3).strip())
                i += 1
            add_block(
                Block(
                    block_id=new_id("blk"),
                    type="list",
                    content=items,
                )
            )
            continue

        # --- Paragraph (consume until blank / special) ---
        para_lines: list[str] = [stripped]
        i += 1
        while i < n:
            nxt = lines[i]
            nxt_stripped = nxt.strip()
            if not nxt_stripped:
                break
            if (
                is_heading(nxt_stripped)
                or is_fence(nxt_stripped)
                or is_list_item(nxt)
                or (
                    "|" in nxt_stripped
                    and i + 1 < n
                    and is_table_separator(lines[i + 1].strip())
                )
            ):
                break
            para_lines.append(nxt_stripped)
            i += 1
        add_block(
            Block(
                block_id=new_id("blk"),
                type="paragraph",
                content=" ".join(para_lines),
            )
        )

    if not sections:
        ensure_section()

    if title is None:
        title = fallback_title or (sections[0].heading if sections else None)

    return title, sections
