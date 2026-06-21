"""Settings, loaded from .env at the project root.

Every module reads configuration from here, never from os.environ directly.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# Project root = one level up from this file (src/config.py).
PROJECT_ROOT = Path(__file__).resolve().parents[1]

load_dotenv(PROJECT_ROOT / ".env")


def _path(value: str) -> Path:
    """Resolve a possibly-relative path against the project root."""
    p = Path(value)
    return p if p.is_absolute() else PROJECT_ROOT / p


def _env(name: str, default: str) -> str:
    """Env var with a default, guarding against an empty value or a leftover inline
    comment (e.g. `JUDGE_MODEL=  # set this`) being read as the value."""
    value = (os.getenv(name) or "").strip()
    return default if not value or value.startswith("#") else value


@dataclass(frozen=True)
class Settings:
    # Dataset
    dataset_repo: str = "ameau01/synthetic-it-support-tickets"
    hf_home: Path = field(default_factory=lambda: _path(os.getenv("HF_HOME", ".hf_cache")))
    hf_token: str | None = field(default_factory=lambda: os.getenv("HF_TOKEN"))

    # Operational data store (SQLite)
    operational_store: Path = field(
        default_factory=lambda: _path(os.getenv("OPERATIONAL_STORE", ".operational_store"))
    )

    # Mode: "mock" replays fixtures, "live" calls real models.
    pipeline_mode: str = field(default_factory=lambda: os.getenv("PIPELINE_MODE", "mock"))

    # Qdrant (hybrid index: dense + sparse vectors, native fusion)
    qdrant_url: str = field(
        default_factory=lambda: os.getenv("QDRANT_URL", "http://localhost:6333"))
    qdrant_api_key: str | None = field(
        default_factory=lambda: os.getenv("QDRANT_API_KEY"))
    qdrant_collection: str = field(
        default_factory=lambda: os.getenv("QDRANT_COLLECTION", "itsm_tickets"))
    # QDRANT_LOCAL=true (default) runs Qdrant embedded on disk at LOCAL_VECTOR_DB_PATH
    #             =false connects to a server at QDRANT_URL (local Docker or Qdrant Cloud).
    qdrant_local: bool = field(
        default_factory=lambda: _env("QDRANT_LOCAL", "true").lower() in ("1", "true", "yes"))
    local_vector_db_path: Path = field(
        default_factory=lambda: _path(os.getenv("LOCAL_VECTOR_DB_PATH", ".vector_db")))

    # Models
    anthropic_api_key: str | None = field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY"))
    openai_api_key: str | None = field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))
    curation_model: str = field(
        default_factory=lambda: os.getenv("CURATION_MODEL", "claude-haiku-4-5-20251001")
    )
    # DeepEval judge: OpenAI frontier by default
    judge_provider: str = field(default_factory=lambda: os.getenv("JUDGE_PROVIDER", "openai"))
    judge_model: str = field(default_factory=lambda: _env("JUDGE_MODEL", "gpt-5.4"))
    judge_n_runs: int = field(default_factory=lambda: int(_env("JUDGE_N_RUNS", "3")))
    embedding_model: str = field(
        default_factory=lambda: os.getenv(
            "EMBEDDING_MODEL", "Snowflake/snowflake-arctic-embed-l-v2.0"
        )
    )
    # Hybrid retrieval: dense (Arctic, 1024-d, 8192 ctx) + sparse (BM25) fused with RRF. 
    #  - dense model supports 8192 tokens but defaults to truncating at 512.
    embedding_dim: int = field(default_factory=lambda: int(_env("EMBEDDING_DIM", "1024")))
    sparse_model: str = field(default_factory=lambda: _env("SPARSE_MODEL", "Qdrant/bm25"))


    # Serve-time relevance gate: 
    #  - if its dense cosine clears this floor, keeps weak or off-topic queries from padding results.
    #  - This is the per-result cutoff. See docs/retrieval-evaluation.md
    cosine_relevance_floor: float = field(
        default_factory=lambda: float(_env("COSINE_RELEVANCE_FLOOR", "0.50")))

    # Abstention floor:
    #  - Derived from abstention_percentile and decides whether the whole query has any answer.
    #  - See docs/retrieval-evaluation.md
    abstention_percentile: float = field(
        default_factory=lambda: float(_env("ABSTENTION_PERCENTILE", "5.0")))


settings = Settings()
