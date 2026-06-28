#!/usr/bin/env sh
# refresh_wiki_snapshot.sh — regenerate the COMMITTED mkdocs/ pages from the current curation.
#
# This is what makes `docker compose up --build wiki-demo` serve the latest content: wiki-demo
#
#   uv run sh scripts/refresh_wiki_snapshot.sh                # render from the current operational store
#   uv run sh scripts/refresh_wiki_snapshot.sh --from-seeds   # (re)load db_seeds first, then render
#
# After it runs, review `git diff mkdocs/` and commit; then rebuild wiki-demo.
set -e

if [ "${1:-}" = "--from-seeds" ]; then
  echo "[refresh_wiki] loading operational store from committed seeds (db_seeds/) …"
  uv run --no-sync sh scripts/load_seeds.sh
fi

echo "[refresh_wiki] rendering the committed mkdocs/ snapshot from the operational store …"
PYTHONPATH=src uv run --no-sync python3 -m wiki.render --mkdocs-dir mkdocs

echo
echo "[refresh_wiki] done. Review and check in:"
echo "    git diff --stat mkdocs/"
echo "    git add mkdocs/docs mkdocs/mkdocs.yml && git commit -m 'Refresh wiki snapshot'"
echo "    docker compose up --build wiki-demo      # serve the latest"
