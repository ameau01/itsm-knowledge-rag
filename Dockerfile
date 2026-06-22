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

# 1) Dependencies first, for layer caching. Only the lockfiles invalidate this layer.
COPY pyproject.toml uv.lock ./
RUN uv sync --no-install-project --group retrieval --group app

# 2) Project source, then install the project itself into the synced environment.
COPY . .
RUN uv sync --group retrieval --group app

# 3) Bake presidio's spaCy model into the image. Otherwise redaction downloads it (~382 MB)
#    at first ingest into the container layer, where it is lost on every recreate and re-fetched.
RUN uv run python -m spacy download en_core_web_lg

# Use the environment built above as-is at runtime: every `uv run` in the entrypoint and the
# scripts should skip re-syncing (no project rebuild, no bytecode recompile on each call).
ENV UV_NO_SYNC=1

# The app serves on SUPPORT_VIEW_PORT (default 8000).
EXPOSE 8000

ENTRYPOINT ["sh", "scripts/docker_entrypoint.sh"]
