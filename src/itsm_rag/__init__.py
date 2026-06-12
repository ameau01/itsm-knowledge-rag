"""ITSM Knowledge RAG: turns closed IT tickets into searchable, verifiable answers — PII redaction at ingest, hybrid retrieval (Qdrant, dense + sparse), LLM-curated overviews."""

# Single source of truth for the version is pyproject.toml.
from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("itsm-knowledge-rag")
except PackageNotFoundError:  # running from a checkout without install
    __version__ = "0.0.0"
