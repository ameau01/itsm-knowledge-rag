# syntax=docker/dockerfile:1
# Image for the ITSM Knowledge Search app: ingest -> embed -> serve, all inside the container.
# Used by the `demo` (mock) and `live` services in docker-compose.yml. It talks to the
# `qdrant` service over the network, so there is no embedded on-disk lock to worry about.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_FROZEN=1

# Toolchain. build-essential/git cover any package that needs to compile; curl is used by the
# entrypoint to wait on Qdrant.
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential git curl \
    && rm -rf /var/lib/apt/lists/*

# uv: the project's package manager. Pin a digest in production; latest is fine for a demo.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# FASTEMBED_CACHE_PATH is NOT a volume, so the baked BM25 model lives in the image layer.
ENV HF_HOME=/app/.hf_cache \
    FASTEMBED_CACHE_PATH=/app/.fastembed_cache

# Pre-baked --group flags (not a bare list): beefy default = everything (rag-live + wiki-live);
ARG SYNC_GROUPS="--group retrieval --group app --group wiki"

# 1) Dependencies first, for layer caching. Only the lockfiles (+ SYNC_GROUPS) invalidate this.
COPY pyproject.toml uv.lock ./
RUN uv sync --no-install-project ${SYNC_GROUPS}

# 2) Project source, then install the project itself into the synced environment.
COPY . .
RUN uv sync ${SYNC_GROUPS}

# 3) Bake presidio's spaCy model into the image. --no-sync: a bare `uv run` would re-sync to the
#    DEFAULT groups and STRIP the optional groups (retrieval/app/wiki) just installed above.
RUN uv run --no-sync python -m spacy download en_core_web_lg

# 3b) Bake the dense + sparse embedding models into the image (into $HF_HOME) 
RUN uv run --no-sync python -c "import sys; sys.path.insert(0, 'src'); \
from retrieval.embeddings import DenseEmbedder, SparseEmbedder; \
DenseEmbedder(); SparseEmbedder(); print('embedders baked into', __import__('os').environ.get('HF_HOME'))"

# 4) Fail the BUILD (not production) if the groups didn't actually land. retrieval -> qdrant_client,
#    app -> streamlit; both are present in every image built from this file (beefy and rag-demo).
RUN uv run --no-sync python -c "import qdrant_client, streamlit; print('deps OK:', qdrant_client.__name__, streamlit.__name__)"

# Use the environment built above as-is at runtime: every `uv run` in the entrypoint.
ENV UV_NO_SYNC=1

# The app serves on SUPPORT_VIEW_PORT (default 8000).
EXPOSE 8000

ENTRYPOINT ["sh", "scripts/docker_entrypoint.sh"]
