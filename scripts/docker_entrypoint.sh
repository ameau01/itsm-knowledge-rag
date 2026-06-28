#!/usr/bin/env sh
# docker_entrypoint.sh — build (if needed) and serve, inside the container.
#
# Used by the demo (mock) and live services in docker-compose.yml. It talks to the qdrant
# service over the network (QDRANT_LOCAL=false), so there is no embedded on-disk lock.
# PIPELINE_MODE (mock | live) selects how the L2 overview is produced during ingest.
#
# Idempotent: the operational store and the Qdrant collection persist across restarts
# (named volumes / the qdrant service), so a second start skips straight to serving.
# ─────────────────────────────────────────────────────────────────────────────
set -e

PORT="${SUPPORT_VIEW_PORT:-8000}"
STORE="${OPERATIONAL_STORE:-.operational_store}"
QURL="${QDRANT_URL:-http://qdrant:6333}"

# 1) Wait for the qdrant service to accept connections.
echo "[entrypoint] waiting for Qdrant at $QURL …"
i=0
until curl -sf "$QURL/readyz" >/dev/null 2>&1; do
  i=$((i + 1))
  [ "$i" -gt 90 ] && { echo "[entrypoint] Qdrant not ready after 90s"; exit 1; }
  sleep 1
done
echo "[entrypoint] Qdrant is ready."

# 2) Operational store. PIPELINE_MODE selects how TICKETS are sourced; the L2 content
#    (curation + overview) ALWAYS comes from the committed SQL seeds (db_seeds/), so neither
#    image ever needs an LLM key.
#      mock  → tickets + L2 entirely from SQL seeds (no HF, no redaction, no key)
#      live  → tickets from HF + redaction, then L2 applied from the SQL seeds
MODE="${PIPELINE_MODE:-mock}"
if [ "$MODE" = "live" ]; then
  # live: HF ingest is expensive, so keep it idempotent (skip if the store already exists).
  if [ -f "$STORE/itsm_rag.db" ]; then
    echo "[entrypoint] LIVE: operational store present — skipping HF ingest"
  else
    echo "[entrypoint] LIVE: ingesting tickets from HF (redact) …"
    uv run --no-sync sh scripts/run_ingest.sh
    echo "[entrypoint] LIVE: applying L2 curation + overview from SQL seeds …"
    uv run --no-sync sh scripts/load_seeds.sh --l2-only
  fi
else
  # mock: loading from SQL seeds is cheap, so ALWAYS (re)load. This guarantees curation + overview
  # are present even when the op_store volume is reused from an earlier run (the stale-volume trap).
  echo "[entrypoint] MOCK: (re)loading store from SQL seeds (no HF, no redaction, no key) …"
  uv run --no-sync sh scripts/load_seeds.sh
fi

# 3) Embedding index — build only if the collection is absent in Qdrant.
if uv run --no-sync python3 - <<'PY'
import sys
sys.path.insert(0, "src")
from retrieval.qdrant_ops import QdrantOps
ops = QdrantOps()
sys.exit(0 if ops.client.collection_exists(ops.collection) else 1)
PY
then
  echo "[entrypoint] vector collection present — skipping index build"
else
  echo "[entrypoint] building embedding index (model baked into the image; this embeds the corpus) …"
  uv run --no-sync sh scripts/build_retrieval_index.sh
fi

# 4) Serve. Bind 0.0.0.0 so the port is reachable from the host.
echo "[entrypoint] serving on 0.0.0.0:$PORT"
exec uv run --no-sync streamlit run streamlit_app/Home.py \
  --server.address 0.0.0.0 --server.port "$PORT" --server.fileWatcherType none
