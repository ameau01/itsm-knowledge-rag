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


@dataclass(frozen=True)
class Settings:
    # Dataset
    dataset_repo: str = "ameau01/synthetic-it-support-tickets"
    hf_home: Path = field(default_factory=lambda: _path(os.getenv("HF_HOME", ".hf_cache")))
    hf_token: str | None = field(default_factory=lambda: os.getenv("HF_TOKEN"))

    # Mode: "mock" replays fixtures, "live" calls real models.
    pipeline_mode: str = field(default_factory=lambda: os.getenv("PIPELINE_MODE", "mock"))

    # Qdrant (hybrid index: dense + sparse vectors, native fusion)
    qdrant_url: str = field(
        default_factory=lambda: os.getenv("QDRANT_URL", "http://localhost:6333"))
    qdrant_api_key: str | None = field(
        default_factory=lambda: os.getenv("QDRANT_API_KEY"))
    qdrant_collection: str = field(
        default_factory=lambda: os.getenv("QDRANT_COLLECTION", "itsm_tickets"))

    # Models
    anthropic_api_key: str | None = field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY"))
    curation_model: str = field(
        default_factory=lambda: os.getenv("CURATION_MODEL", "claude-haiku-4-5-20251001")
    )
    judge_model: str | None = field(default_factory=lambda: os.getenv("JUDGE_MODEL") or None)
    embedding_model: str = field(
        default_factory=lambda: os.getenv(
            "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
        )
    )


settings = Settings()
