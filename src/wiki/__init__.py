"""Wiki domain: the curation-result loader.

Reads the curation output (produced by the external generation step) and writes ONLY the
generated column (curated_description) into the operational store's wiki_pages table.
The deterministic columns are ingest's.
"""
