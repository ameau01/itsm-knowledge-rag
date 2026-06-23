#!/usr/bin/env sh
# run_wiki.sh — serve the MkDocs wiki on WIKI_VIEW_PORT (docker entrypoint for wiki-demo/wiki-live).
#
# PIPELINE_MODE:
#   mock  — serve the committed mkdocs/ pages as-is (no ingest, no DB, no key, no build). Fast.
#   live  — ingest tickets (if the store is missing), optionally load curation from
#           $CURATION_DIR, then build the wiki from scratch into the ephemeral .mkdocs/
#           (prune + copy template + render from the store) and serve THAT.
#           (Curation generation stays in the external experiment; without a curation dir the
#            live pages show deterministic diagnostics + a "Curation pending" placeholder.)
#
# Live never overwrites the committed mkdocs/ — it builds and serves .mkdocs/.
# The wiki reads the operational store, not Qdrant — so no qdrant dependency.
set -e

PORT="${WIKI_VIEW_PORT:-8001}"
MODE="${PIPELINE_MODE:-mock}"
STORE="${OPERATIONAL_STORE:-.operational_store}"

if [ "$MODE" = "live" ]; then
  if [ -f "$STORE/itsm_rag.db" ]; then
    echo "[run_wiki] operational store present — skipping ingest"
  else
    echo "[run_wiki] ingesting corpus (redact + seed wiki_pages) …"
    uv run sh scripts/run_ingest.sh
  fi
  if [ -n "${CURATION_DIR:-}" ] && [ -d "$CURATION_DIR" ]; then
    echo "[run_wiki] loading curation from $CURATION_DIR …"
    uv run sh scripts/load_wiki.sh --curation-dir "$CURATION_DIR" || true
  fi
  echo "[run_wiki] building wiki from scratch into .mkdocs …"
  rm -rf .mkdocs
  cp -r mkdocs .mkdocs
  PYTHONPATH=src uv run --group wiki python3 -m wiki.render --mkdocs-dir .mkdocs
  echo "[run_wiki] serving LIVE build on 0.0.0.0:$PORT (.mkdocs)"
  exec uv run --group wiki mkdocs serve -f .mkdocs/mkdocs.yml -a "0.0.0.0:$PORT"
fi

echo "[run_wiki] serving committed pages on 0.0.0.0:$PORT (mkdocs)"
exec uv run --group wiki mkdocs serve -f mkdocs/mkdocs.yml -a "0.0.0.0:$PORT"
