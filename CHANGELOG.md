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

## [Initial ingest code with redaction]

### Changed
- update design doc to include sqlite operational store.
- refactory src code to flatten itsm_rag.

### Added
- Added initial ingest code to download from huggingface
- Add redaction_policy.yaml to remove PII
- Add test scripts to run presidio redaction and examine pii.json and retention.json from dataset.

### Documentation
- `docs/operational-store.md`, `ARCHITECTURE.md`

## [Redaction Code Refactory]
- Modify redaction policy to use AD dictectory user list for redaction.

### Added
- Add measurement script to score redaction effectiveness with PII and rentetion score
- Add more columns from ticket corpus to operation store

### Changed
- redaction-policy updated to use AD directory list.
- update redactor code to use AD directory, and then custom policy and then presidio.

### Documentation
- `docs/evaluation.md`, `docs/redaction-policy.md`, `README.md`

## [Retrieval Evaluatoin implementation]

### Added
- Using the eval-set, add code to run recall using root-cause as measurement without LLM.
- Using the eval-set, add code to run contextual evaluation with DeepEval framework with OpenAI LLM.

### Changed
- Change the evaluation script into two scripts: run_classic_evaluation.sh, run_deepeval_evaluation.s

### Documentation
- `docs/evaluation.md`, `docs/redaction-evaluation.md`, `docs/retrieval-evaluation.md`

## [Curation Evaluation implementation]

### Added
- Using DeepEval test case to evaluate quality of wiki pages.
- Using G-Eval custom query to evaluate quality of AI overview
- Added ai-overview component to streamlit search page.

### Documentation
- `docs/running.md`, `docs/wiki-evaluation.md`

