# Running the system

Three paths, by how much you want to run. For what the system does, see the [README](../README.md). For how it works, see [ARCHITECTURE.md](../ARCHITECTURE.md).

The pattern: everything upstream and downstream of the model call is identical across modes. Only the LLM client swaps. A live client calls a real model. A mock client replays recorded fixtures. The same pipeline, index, redaction, and eval run in every mode.


## Path A: Docker, mock mode

No LLM, no API key, no network. The fastest way to see the system run.

```
docker compose up --build demo
```

This replays recorded fixtures through the real pipeline and serves the two views at localhost. The output carries a MOCK MODE banner so it is never mistaken for live generation. `--build` is defensive: it picks up any source change since the last run and is a near-instant cache hit when nothing changed.

Use this to see the search interface, the overview-plus-sources layout, and the two views, without any setup.


## Path B: Docker, live LLM

Real model, real generation. Needs Docker, internet, and an API key.

```
cp .env.example .env && $EDITOR .env   # add the API key
docker compose up --build live
```

First run builds the image and fetches the dataset from Hugging Face (about 12 MB). Subsequent runs are faster. This runs the full pipeline live: redaction, curation, indexing, and serving.


## Path C: local, developer

For working on the code. Needs a local Python toolchain and an API key.

```
uv sync
cp .env.example .env && $EDITOR .env
make ingest      # redact, curate, index
make serve       # start the two views
make eval        # run the four-axis eval
```

`make help` lists the rest: the hybrid ablation, the cache-versus-zero-shot head-to-head, and the leakage check on its own.


## What you will see

Both Docker paths serve two surfaces. The IT support view is the full search: type a problem, get the cached overview on top and ranked source tickets below. The employee view is the redaction-safe, browse-only wiki.

The support view is a recommender. It surfaces how similar issues were resolved. It does not take a new ticket or decide a match. The agent reads the result and judges whether it fits. See [ARCHITECTURE.md](../ARCHITECTURE.md).


## The static demo

A keyless static demo runs on GitHub Pages with recorded fixtures, for a quick look with no install. See the repo's Pages link. Worked examples of real output (a query, its overview, the source tickets, the redaction applied) are in [examples/](../examples/).
