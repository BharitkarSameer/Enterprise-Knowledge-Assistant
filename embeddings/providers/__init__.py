"""Embedding providers (OpenAI, Ollama, Sentence Transformers, etc.)."""

from embeddings.providers.sentence_transformer import (
    DEFAULT_MODEL,
    SentenceTransformerProvider,
)

__all__ = ["DEFAULT_MODEL", "SentenceTransformerProvider", "get_default_provider"]


def get_default_provider() -> SentenceTransformerProvider:
    return SentenceTransformerProvider()
