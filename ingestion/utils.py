"""Ingestion helpers."""

import os


def get_extension(filename: str) -> str:
    return os.path.splitext(filename)[1].lower()
