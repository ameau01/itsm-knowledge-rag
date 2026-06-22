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

# 2) Operational store (redacted tickets). PIPELINE_MODE controls L2 curation (mock|live).
if [ -f "$STORE/itsm_rag.db" ]; then
  echo "[entrypoint] operational store present — skipping ingest"
else
  echo "[entrypoint] ingesting corpus (redact, mode=${PIPELINE_MODE:-mock}) …"
  uv run sh scripts/run_ingest.sh
fi

# 3) Embedding index — build only if the collection is absent in Qdrant.
if uv run --group retrieval python3 - <<'PY'
import sys
sys.path.insert(0, "src")
from retrieval.qdrant_ops import QdrantOps
ops = QdrantOps()
sys.exit(0 if ops.client.collection_exists(ops.collection) else 1)
PY
then
  echo "[entrypoint] vector collection present — skipping index build"
else
  echo "[entrypoint] building embedding index (downloads the model once, ~2 GB) …"
  uv run sh scripts/build_retrieval_index.sh
fi

# 4) Serve. Bind 0.0.0.0 so the port is reachable from the host.
echo "[entrypoint] serving on 0.0.0.0:$PORT"
exec uv run --group app --group retrieval streamlit run streamlit_app/Home.py \
  --server.address 0.0.0.0 --server.port "$PORT" --server.fileWatcherType none
