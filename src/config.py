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
    comment (e.g. `JUDGE_MODEL=  # decision pending`) being read as the value."""
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


settings = Settings()
