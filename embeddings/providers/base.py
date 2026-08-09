"""Embedding provider protocol."""

from __future__ import annotations

from typing import Protocol


class EmbeddingProvider(Protocol):
    """Swap Sentence Transformers / Ollama / OpenAI behind this interface."""

    model_name: str

    @property
    def dimensions(self) -> int: ...

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts into dense vectors."""
        ...
