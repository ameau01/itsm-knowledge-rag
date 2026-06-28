# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Vector store swap] Replace pgvector with Qdrant.

### Changed
- Hybrid retrieval now uses Qdrant: dense + sparse vectors with native server-side
  fusion in a single query, replacing Postgres/pgvector + application-side BM25.
- Updated throughout: ARCHITECTURE.md diagrams, docs/retrieval.md,
  docs/evaluation.md ablation wording (sparse-only arm), .env.example
  (QDRANT_URL/COLLECTION replace DATABASE_URL), src config, .gitignore volumes.
- eval-set metrics contract is implementation-neutral (sparse/dense/hybrid arms);
  no eval-set changes required.

## [Project initi] Add initial design docs.
### Added
- Created project skeletion with `pyproject.toml`, `requirement.txt`, `env.example`
- Added MIT standard license 

### Documentation
- `ARCHITECTURE.md` and `README.md`

## [Design Doc Refactory] Update repo with new design.

### Changed
- Dropped the governance framing because core user is the support agent, who has full privileges.
- Dropped knowledge graph in design, because it add a layer hybird retrieval cannot support.
- Dropped LLM router. New query path is simple with AI overviews and sources.

### Added
- Add supporting design doc under `docs\` folder  

### Documentation
- `ARCHITECTURE.md`, `README.md`, `docs/datataset.md`, `docs/evaluation.md`, `docs/redaction-policy.md`, `docs/retrieval.md`, `docs/running.md`

## [Curation Langraph Implementation]

### Added
- Added curation langraph source code
- Added AI overview curation source code

### Changed
- Updated evaluation measurement result

### Documentation
- `docs/wiki-evaluation.md`, `docs/wiki-curation.md`

## [Live Demo and Live WIki page]

### Added 
- Added live github page with mkdocs
- Added live streamlit app demo page with Qdrant cloud vector db.
- Change release version to 1.0.0

### Documentation
- `README.md`
