# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
