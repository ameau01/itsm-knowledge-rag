"""Operational store: the shared SQLite source of truth (tickets + wiki_pages).

Imported by ingest (writes tickets + seeds wiki_pages), the wiki curation load
(fills curated_description), and the retrieval index build (reads tickets).
"""
