"""Sentence Transformers embedding provider (local)."""

from __future__ import annotations

DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


class SentenceTransformerProvider:
    """
    Local embeddings via sentence-transformers.

    First call downloads the model; later calls reuse the in-memory instance.
    """

    def __init__(self, model_name: str = DEFAULT_MODEL) -> None:
        self.model_name = model_name
        self._model = None
        self._dimensions: int | None = None

    def _load(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name)
            # Probe dimension once
            probe = self._model.encode(["dimension probe"], normalize_embeddings=True)
            self._dimensions = int(probe.shape[1])
        return self._model

    @property
    def dimensions(self) -> int:
        self._load()
        assert self._dimensions is not None
        return self._dimensions

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        model = self._load()
        vectors = model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return [vector.tolist() for vector in vectors]
