"""Markdown file connector."""

from fastapi import UploadFile


async def parse_markdown(file: UploadFile) -> str:
    """
    Read an uploaded markdown file and return its raw text content.

    Payload is passed to the next layer (processing / chunking).
    """
    content = await file.read()
    return content.decode("utf-8")
