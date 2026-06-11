# ITSM Knowledge RAG

[![Status](https://img.shields.io/badge/status-v0.0.2%20initial%20design-orange)](#project-status)
[![License: MIT](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![python](https://img.shields.io/badge/python-3.11+-blue)](https://www.python.org)
[![Dataset](https://img.shields.io/badge/Dataset-synthetic--it--support--tickets-yellow)](https://huggingface.co/datasets/ameau01/synthetic-it-support-tickets)
[![PII](https://img.shields.io/badge/PII-Presidio%20%2B%20custom%20recognizers-orange)](https://microsoft.github.io/presidio/)
[![retrieval](https://img.shields.io/badge/retrieval-pgvector%20%2B%20BM25-blueviolet)](https://github.com/pgvector/pgvector)
[![eval](https://img.shields.io/badge/eval-DeepEval%20%2F%20G--Eval-9cf)](https://github.com/confident-ai/deepeval)

**Turns a company's closed IT tickets into searchable, verifiable answers, so problems that have already been solved don't get solved from scratch again. It recommends; the agent decides.**


## The problem

In any organization, the same IT issues recur constantly. An employee's VPN drops right after approving MFA. An account locks minutes after a password reset. A device fails certificate validation. Each time, a support engineer diagnoses the cause, applies a fix, and closes the ticket. Each time, that knowledge effectively disappears.

It is not lost, exactly. It is just unreachable. It sits across thousands of closed tickets. The same issue is described a dozen different ways, padded with back-and-forth correspondence, and mixed with personal data. Nobody re-reads closed tickets. So when the same problem comes in next week, it gets diagnosed from scratch, even though the organization already knows the answer.

The cost lands on both sides. Agents re-solve known issues. Employees wait on answers the company already has.


## What it does

This project makes an organization's own resolution history usable again. It is a recommender for human agents, not an auto-resolver.

The system never sees the new ticket. The agent does. When a new ticket arrives, the agent reads it, searches the system for the issue it resembles, and gets back a concise overview of how this company resolved that issue before. The overview gives the common symptoms, the root cause its engineers identified, and the steps that worked. Beneath it sit the original source tickets. The agent reviews them, decides whether the new ticket is genuinely the same problem, and reuses the proven resolution if it fits.

The judgment stays with the agent. The system surfaces prior knowledge and ranks the evidence. It does not classify the new ticket, declare a match, or apply a fix. That separation is deliberate. Deciding whether two tickets are the same problem is exactly the call a human should make before touching a system.

The distinction from a general-purpose model matters here. A general model can describe standard VPN troubleshooting. It cannot know that in this corporate environment the disconnect was an expired device certificate fixed through the internal enrollment service. That fact exists only in the company's own tickets. This project surfaces that organization-specific, proven knowledge. It exists nowhere else.


## How it works

Closed tickets run through a pipeline. The result is served through a search interface modeled on the familiar "AI overview, then sources" pattern. The full design is in [ARCHITECTURE.md](ARCHITECTURE.md).

**Redaction runs first, over the whole ticket.** No personal data reaches the searchable layer or any published surface. A declarative policy is enforced with Presidio plus custom recognizers for corporate identifier formats that off-the-shelf detection misses. Redacting first also removes the person-specific tokens that would otherwise stop curation from generalizing. See [docs/redaction-policy.md](docs/redaction-policy.md).

**Curation consolidates the messy fields.** Users describe the same problem many ways. Curation turns those descriptions into one common, searchable issue statement. The human-determined root cause and resolution are surfaced verbatim, not regenerated. The system organizes the questions. It does not rewrite the answers. See [docs/retrieval.md](docs/retrieval.md).

**Retrieval is hybrid, and the overview is cached.** Hybrid search (pgvector + BM25) matches a query to the right issue family. The overview is precomputed per family, so a search returns a prepared answer instead of generating one on every query. The cached overview is the same idea as a Google "AI overview," but precomputed because the corpus is bounded. See [docs/retrieval.md](docs/retrieval.md).

**Two surfaces share one pipeline.** Support agents get the full search: the overview plus ranked source tickets they are authorized to read. General employees get a redaction-safe, browse-only version of the same curated knowledge.


## Results

Measured on a synthetic corpus of 745 tickets across 15 issue families. Full methodology and per-axis detail in [docs/evaluation.md](docs/evaluation.md).

| Axis | Metric | Result |
|---|---|---|
| PII leakage (deterministic) | leak rate vs. authored sidecar | TBD |
| Technical retention | RETAIN-class strings preserved | TBD |
| Retrieval | recall@k, nDCG@k | TBD |
| Curation quality (judge-based) | faithfulness, citation accuracy | TBD |
| Cache vs. zero-shot | latency, cost per query | TBD |

The PII-leakage check is the one hard, non-circular number. Its ground truth is authored upstream, independently of the redaction system being tested, so the redactor cannot grade itself. The curation metrics are judge-based and reported as such. The project is explicit about which guarantees are deterministic and which are interpretive.


## Quick start

Three paths. Full detail in [docs/running.md](docs/running.md).

**Path A. Docker, mock mode (no LLM, no key, no network).**
```
docker compose up --build demo
```
Replays recorded fixtures through the real pipeline. The output carries a MOCK MODE banner.

**Path B. Docker, live LLM.**
```
cp .env.example .env && $EDITOR .env   # add the API key
docker compose up --build live
```

**Path C. Local, developer.**
```
uv sync
cp .env.example .env && $EDITOR .env
make demo
```


## Scope

This is a focused system, not a platform. It runs on a single ITSM ticket corpus. It uses one inexpensive model throughout. It is not agentic. There is no tool use and no autonomous orchestration. Curation organizes problem descriptions. It preserves the root causes and resolutions human engineers determined rather than arbitrating them. The architecture is deliberately simple. The evaluation is where the rigor goes. The reasoning behind these and other choices is in [docs/decisions.md](docs/decisions.md).


## Dataset

A synthetic ITSM corpus of 745 tickets across 15 issue families. PII is injected into the free-text fields, with an authored ground-truth sidecar (`pii.json`) that backs the deterministic leakage benchmark. The corpus is synthetic by design: it gives controllable ground truth, which is what makes the deterministic eval possible. No real personal data is involved. Published at [`ameau01/synthetic-it-support-tickets`](https://huggingface.co/datasets/ameau01/synthetic-it-support-tickets). Schema and the sidecar contract are in [docs/dataset.md](docs/dataset.md).


## Repo orientation

```
README.md            this file
ARCHITECTURE.md      system design, diagram, the why behind each layer
docs/                retrieval, evaluation, decisions, dataset, redaction-policy, running
src/                 pipeline: redaction, curation, retrieval, serving
eval/                eval harness and results
examples/            real worked outputs: query, overview, source tickets, redaction
```


## Stack

Python, pgvector, BM25, Presidio (with custom recognizers), DeepEval / G-Eval, MkDocs-Material, Docker.


## Project status

[![Version](https://img.shields.io/badge/version-0.0.2-blue)](https://github.com/ameau01/itsm-knowledge-rag/releases)
[![Status: Design](https://img.shields.io/badge/status-initial%20design-orange)](https://github.com/ameau01/itsm-knowledge-rag)

Early stage: The dataset is published and the design is documented. Implementation is in progress.

- Published dataset with an authored PII sidecar: [`ameau01/synthetic-it-support-tickets`](https://huggingface.co/datasets/ameau01/synthetic-it-support-tickets).
- Initial design documentation on docs/ folder.

## License

MIT.


## Citation

```
@misc{itsm_knowledge_rag_2026,
  title   = {ITSM Knowledge RAG},
  author  = {Alexander Meau},
  year    = {2026},
  version = {0.0.2}
}
```
