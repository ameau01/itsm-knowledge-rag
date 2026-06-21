"""
Embedders for hybrid retrieval.

  DenseEmbedder   Snowflake Arctic Embed (1024-d). Queries use the model's registered
                  'query' prompt; documents take no prompt. max_seq_length is forced to
                  8192 (the default truncates at 512).
  SparseEmbedder  BM25 sparse vectors via FastEmbed, emitted as Qdrant SparseVectors.

The heavy model libraries (sentence-transformers, fastembed) are imported lazily inside
__init__, so this module imports without them and tests can substitute a fake embedder.
"""

from __future__ import annotations

from qdrant_client import models

from config import settings

_QUERY_PROMPT = "query"


class DenseEmbedder:
    def __init__(self, model_name: str | None = None) -> None:
        from sentence_transformers import SentenceTransformer  # lazy (pulls torch)

        name = model_name or settings.embedding_model
        self.model = SentenceTransformer(name)
        self.model.max_seq_length = 8192  # default truncates at 512 despite 8192 support
        get_dim = (getattr(self.model, "get_embedding_dimension", None)
                   or self.model.get_sentence_embedding_dimension)
        self.dim = get_dim()
        if self.dim != settings.embedding_dim:
            raise ValueError(
                f"dense model '{name}' has dim {self.dim}, but EMBEDDING_DIM="
                f"{settings.embedding_dim}. Set EMBEDDING_MODEL and EMBEDDING_DIM to match "
                "(Snowflake/snowflake-arctic-embed-l-v2.0 is 1024).")

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self.model.encode(texts, normalize_embeddings=True, show_progress_bar=True).tolist()

    def embed_query(self, text: str) -> list[float]:
        vec = self.model.encode([text], prompt_name=_QUERY_PROMPT, normalize_embeddings=True)
        return vec[0].tolist()


class SparseEmbedder:
    def __init__(self, model_name: str | None = None) -> None:
        from fastembed import SparseTextEmbedding  # lazy

        self.model = SparseTextEmbedding(model_name or settings.sparse_model)

    @staticmethod
    def _to_vector(emb) -> models.SparseVector:
        return models.SparseVector(indices=emb.indices.tolist(), values=emb.values.tolist())

    def embed_documents(self, texts: list[str]) -> list[models.SparseVector]:
        from tqdm import tqdm
        return [self._to_vector(e)
                for e in tqdm(self.model.embed(texts), total=len(texts), desc="sparse")]

    def embed_query(self, text: str) -> models.SparseVector:
        return self._to_vector(next(iter(self.model.query_embed([text]))))
