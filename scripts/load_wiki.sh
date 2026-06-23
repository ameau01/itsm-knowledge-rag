#!/usr/bin/env sh
# load_wiki.sh — load curation output into wiki_pages.curated_description.
#
#   uv run sh scripts/load_wiki.sh --curation-dir <dir>
#
# Reads the external generation step's curation files and fills the generated column (curated_description) for each page.
# Prereq: run the ingest pipeline first so wiki_pages rows exist.
set -e
uv run python3 src/wiki/load.py "$@"
