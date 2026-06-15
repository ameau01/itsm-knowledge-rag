"""
Redaction benchmark

Scores the PolicyRedactor against the two authored ground-truth sidecars:
  pii.json       — REMOVE answer key (PII recall)
  retention.json — KEEP answer key   (retention / over-redaction)

Both sidecars are loaded from the HF snapshot (same source as the corpus).
The redactor itself does NOT see these files at runtime — they are eval
artefacts only.

Usage (from project root)
-------------------------
    uv run python3 -m ingest.score                   # all 745 tickets
    uv run python3 -m ingest.score --family AIT      # single family
    uv run python3 -m ingest.score --no-presidio     # L1+L2 only
    uv run sh scripts/score_redaction.sh             # convenience wrapper

Output
------
    PII RECALL table   — % of pii.json values absent from redacted text
    RETENTION table    — % of retention.json values still present after redaction
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import pandas as pd

_SRC = Path(__file__).parent.parent
sys.path.insert(0, str(_SRC))

from corpus.extractor import extract_text_fields          # noqa: E402
from ingest.redactor import PolicyRedactor                # noqa: E402

_HF_CACHE  = _SRC.parent / ".hf_cache"
_SNAPSHOTS = _HF_CACHE / "datasets--ameau01--synthetic-it-support-tickets" / "snapshots"
_EVAL_DIR  = _SRC.parent / "eval-set" / "redaction"
_POLICY    = _SRC / "ingest" / "redaction_policy.yaml"


# ── Dataset helpers ────────────────────────────────────────────────────────────

def _latest_snapshot() -> Path:
    if not _SNAPSHOTS.exists():
        sys.exit(
            "HF snapshot not found. Run: uv run sh scripts/test_hf_download.sh"
        )
    snaps = sorted(_SNAPSHOTS.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
    if not snaps:
        sys.exit("HF snapshot directory is empty.")
    return snaps[0]


def _load_parquet(snap: Path, family: str | None) -> pd.DataFrame:
    df = pd.read_parquet(snap / "data" / "train.parquet")
    if family and family != "ALL":
        df = df[df["record_id"].str.split("-").str[1] == family]
    return df


def _find_sidecar(snap: Path, filename: str) -> Path:
    """Prefer HF snapshot, fall back to local eval-set/."""
    candidate = snap / filename
    if candidate.exists():
        return candidate
    local = _EVAL_DIR / filename
    if local.exists():
        return local
    raise FileNotFoundError(
        f"{filename} not found in HF snapshot or {_EVAL_DIR}.\n"
        "Run: uv run sh scripts/test_hf_download.sh"
    )


def _load_users_directory(snap: Path) -> dict:
    candidate = snap / "users_directory.json"
    if candidate.exists():
        return json.loads(candidate.read_text())
    raise FileNotFoundError(
        "users_directory.json not found in HF snapshot. "
        "Run: uv run sh scripts/test_hf_download.sh"
    )


# ── Scoring ────────────────────────────────────────────────────────────────────

_PII_ORDER = ["email", "emp_id", "hostname", "ip", "location", "person", "phone", "username"]


def _print_report(
    family: str,
    scored: int,
    all_pii: dict[str, list[tuple[str, bool]]],
    all_ret: dict[str, list[tuple[str, bool]]],
    l1_only: bool,
) -> None:
    mode = "L1+L2 only" if l1_only else "L1+L2+L3 (Presidio)"
    print(f"\n{'═' * 60}")
    print(f"  Family: {family}  |  Tickets scored: {scored}  |  Mode: {mode}")
    print(f"{'═' * 60}")

    # PII recall
    print("\nPII RECALL  (✓ ≥ 95%  ~ < 95%  ✗ < 80%)")
    pf = pt = 0
    for t in _PII_ORDER:
        entries = all_pii.get(t, [])
        if not entries:
            continue
        found = sum(1 for _, c in entries if c)
        total = len(entries)
        pct   = 100 * found / total
        mark  = "✓" if pct >= 95 else ("~" if pct >= 80 else "✗")
        print(f"  {mark} {t:15s}  {found:5d}/{total:5d}  {pct:5.1f}%")
        pf += found
        pt += total
    if pt:
        print(f"  {'OVERALL':16s}  {pf:5d}/{pt:5d}  {100*pf/pt:5.1f}%")

    # Retention
    print("\nRETENTION  (✓ ≥ 80%  ~ < 80%)")
    rf = rt = 0
    for t in sorted(all_ret):
        entries = all_ret[t]
        if not entries:
            continue
        found = sum(1 for _, s in entries if s)
        total = len(entries)
        pct   = 100 * found / total
        mark  = "✓" if pct >= 80 else "~"
        print(f"  {mark} {t:22s}  {found:5d}/{total:5d}  {pct:5.1f}%")
        rf += found
        rt += total
    if rt:
        print(f"  {'OVERALL':23s}  {rf:5d}/{rt:5d}  {100*rf/rt:5.1f}%")

    print(f"\n{'─' * 60}\n")


# ── Main ───────────────────────────────────────────────────────────────────────

def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Score the PolicyRedactor against pii.json (PII recall) "
            "and retention.json (over-redaction) ground truth."
        )
    )
    parser.add_argument(
        "--family",
        default="ALL",
        help="Ticket family prefix (AIT, ALP, …) or ALL (default).",
    )
    parser.add_argument(
        "--no-presidio",
        action="store_true",
        help="Disable Layer 3 Presidio NER (AD + format rules only).",
    )
    args = parser.parse_args(argv)

    snap      = _latest_snapshot()
    df        = _load_parquet(snap, args.family)
    directory = _load_users_directory(snap)

    pii_path = _find_sidecar(snap, "pii.json")
    ret_path = _find_sidecar(snap, "retention.json")

    pii_data = {t["ticket_id"]: t["pii_instances"]
                for t in json.loads(pii_path.read_text())}
    ret_raw  = json.loads(ret_path.read_text())
    ret_data = {t["ticket_id"]: t.get("retain_instances", [])
                for t in ret_raw["tickets"]}

    use_presidio = not args.no_presidio
    n_users      = len(directory.get("users", []))
    print(f"\nLoading redaction policy: {_POLICY.name}")
    print(f"  AD directory : {n_users} users (from HF snapshot)")
    print(f"  Presidio L3  : {'yes' if use_presidio else 'no'}")

    redactor = PolicyRedactor(
        policy_path=_POLICY,
        use_presidio=use_presidio,
        directory=directory,
    )

    print(f"\nScoring {args.family} ({len(df)} tickets) …")

    all_pii: dict[str, list[tuple[str, bool]]] = defaultdict(list)
    all_ret: dict[str, list[tuple[str, bool]]] = defaultdict(list)
    scored = 0

    for _, row in df.iterrows():
        tid = row["record_id"]
        if tid not in pii_data:
            continue

        fields     = extract_text_fields(row)
        all_text   = "\n".join(fields.values())
        final_text = redactor.redact(all_text)

        for inst in pii_data.get(tid, []):
            caught = inst["value"] not in final_text
            all_pii[inst["type"]].append((inst["value"], caught))

        for ri in ret_data.get(tid, []):
            survived = ri["value"] in final_text
            all_ret[ri["type"]].append((ri["value"], survived))

        scored += 1
        if scored % 50 == 0:
            print(f"  scored {scored}/{len(df)} …", end="\r")

    _print_report(
        family   = args.family,
        scored   = scored,
        all_pii  = dict(all_pii),
        all_ret  = dict(all_ret),
        l1_only  = args.no_presidio,
    )


if __name__ == "__main__":
    main()
