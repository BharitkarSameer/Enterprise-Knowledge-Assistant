"""
Pipeline orchestrator — CLI entry that reuses the same pipeline service as the API.

Usage (from project root):
    1. Paste your file path into FILE_PATH below
    2. python implementation.py
"""

from __future__ import annotations

import asyncio
import mimetypes
from io import BytesIO
from pathlib import Path

from fastapi import UploadFile
from starlette.datastructures import Headers

from pipeline.service import iter_pipeline

FILE_PATH = r"C:\Users\SAMEER BHARITKAR\Documents\coding\Intelligent_Document_Parser\Enterprise-Knowledge-Assistant\test.md"


def _to_upload_file(file_path: str | Path) -> UploadFile:
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"File not found: {path}")

    data = path.read_bytes()
    mime, _ = mimetypes.guess_type(path.name)
    return UploadFile(
        file=BytesIO(data),
        filename=path.name,
        headers=Headers({"content-type": mime or "application/octet-stream"}),
    )


async def main() -> None:
    upload = _to_upload_file(FILE_PATH)
    async for event in iter_pipeline(upload):
        step = event.get("step")
        status = event.get("status")
        detail = event.get("detail") or {}
        if step == "complete":
            summary = event.get("summary") or {}
            print()
            print("COMPLETE")
            for key, value in summary.items():
                print(f"  {key}: {value}")
            continue
        if status == "running":
            print(f"→ {step} ...")
        elif status == "done":
            print(f"✓ {step}  {detail}")
        elif status == "error":
            print(f"✗ error  {detail}")


if __name__ == "__main__":
    asyncio.run(main())
