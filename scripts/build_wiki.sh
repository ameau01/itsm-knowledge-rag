#!/usr/bin/env sh
# build_wiki.sh — build the wiki into the ephemeral .mkdocs/ (built from scratch each run).
#
#   uv run sh scripts/build_wiki.sh
#
# It NEVER overwrites the committed mkdocs/. It:
#   1) prunes .mkdocs and copies the committed template (mkdocs/) into it
#   2) renders mkdocs pages from the operational store into .mkdocs (overwriting only .mkdocs)
#   3) builds the static site into .mkdocs/site/
# Deterministic, no LLM, no API key. Prereq: an operational store with wiki_pages
# (run scripts/run_ingest.sh, then scripts/load_wiki.sh to fill curated_description).
set -e
rm -rf .mkdocs
cp -r mkdocs .mkdocs
PYTHONPATH=src uv run --group wiki python3 -m wiki.render --mkdocs-dir .mkdocs
uv run --group wiki mkdocs build -f .mkdocs/mkdocs.yml
echo "[build_wiki] built from scratch → .mkdocs/  (committed mkdocs/ untouched)"
