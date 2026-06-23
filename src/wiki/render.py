"""MkDocs compilation: wiki_pages + tickets -> Markdown site under mkdocs/docs/.

Deterministic, no LLM. For each wiki_pages row it renders a Material-for-MkDocs page:
  - curated prose (Description / Root cause / Recommendation) from curated_description
  - the canonical Diagnostics from wiki_pages.diagnostic_steps (already deterministic)
  - Affected-environment stats and 1-2 Resolution examples from the member tickets
Then it writes the home page (index.md) and the explicit nav into mkdocs.yml.

NULL-safe: a page whose curated_description is NULL still renders — environment +
diagnostics from the tickets, with a "Curation pending" note in place of the prose. So the
site is buildable end-to-end straight after ingest, before any curation runs.

Default target is the ephemeral .mkdocs/ build dir (gitignored) — it never overwrites the
committed mkdocs/. Refreshing the committed snapshot is a deliberate `--mkdocs-dir mkdocs`.

Run:
    python -m wiki.render                      # render into .mkdocs (ephemeral)
    python -m wiki.render --mkdocs-dir mkdocs   # deliberately refresh the committed snapshot
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # src/ on the path
from operational_store.store import get_connection  # noqa: E402

_THIS = Path(__file__).resolve()
_PROJECT = _THIS.parent.parent.parent
DEFAULT_MKDOCS = _PROJECT / "mkdocs"      # committed template + snapshot (demo / Pages)
DEFAULT_BUILD = _PROJECT / ".mkdocs"      # ephemeral build dir — default render target
FAMILY_NAMES = _PROJECT / "eval-set" / "wiki" / "family_names.json"


# ── small helpers ──────────────────────────────────────────────────────────────
def slug(root_cause_id: str) -> str:
    return root_cause_id.split("/", 1)[-1]


def humanize(s: str) -> str:
    return s.replace("-", " ").strip().capitalize()


def anchor(text: str) -> str:
    t = re.sub(r"[^\w\s-]", "", text).strip().lower()
    return re.sub(r"[-\s]+", "-", t)


def _as_json(value, default):
    if not value:
        return default
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return value


def load_family_names() -> dict:
    try:
        d = json.loads(FAMILY_NAMES.read_text(encoding="utf-8"))
        return {k: v for k, v in d.items() if not k.startswith("_")}
    except (OSError, json.JSONDecodeError):
        return {}


# ── nature → self_serviceable ────────────────────────────────────────────────────
_IT_NATURE = re.compile(
    r"cert|chain|eap-tls|pki|credential|password|token|lockout|mfa|sso|okta|kerberos|saml|"
    r"mdm|intune|compliance|policy|gpo|entitlement|radius|controller|gateway|load.?balanc|"
    r"dns|resolver|zone|firewall|tunnel|tpm|bitlocker|encryption|protector|enrollment|provision",
    re.I,
)


def self_serviceable(root_cause_id: str, narratives: list[str]) -> int:
    text = root_cause_id.lower() + " " + " ".join(narratives).lower()
    return 0 if _IT_NATURE.search(text) else 1


# ── environment top-3 (normalized) ───────────────────────────────────────────────
def _norm_key(v: str) -> str:
    s = re.sub(r"[\s_\-]+", " ", str(v).strip().lower())
    return re.sub(r"[^a-z0-9 ]", "", s).strip()


def _norm_region(v: str) -> str:
    return re.sub(r"\s*\d+$", "", _norm_key(v)).strip()


def _merge_counts(counter: Counter, norm_fn):
    totals: dict = defaultdict(int)
    surfaces: dict = defaultdict(Counter)
    for surface, cnt in counter.items():
        key = norm_fn(surface)
        if not key:
            continue
        totals[key] += cnt
        surfaces[key][surface] += cnt
    items = [(surfaces[k].most_common(1)[0][0], total) for k, total in totals.items()]
    items.sort(key=lambda x: -x[1])
    return items


def env_top3(members: list[dict]) -> dict:
    raw: dict[str, Counter] = {k: Counter() for k in ("os", "platform", "region", "user_group")}
    for m in members:
        env = _as_json(m.get("environment"), {})
        if isinstance(env, dict):
            for k in raw:
                if env.get(k):
                    raw[k][env[k]] += 1
    dims = {}
    for k, counter in raw.items():
        dims[k] = _merge_counts(counter, _norm_region if k == "region" else _norm_key)[:3]
    return {"n": len(members), "dims": dims}


def _env_block(stats: dict) -> str:
    n = stats["n"]
    labels = {"os": "Operating system", "platform": "Device / platform",
              "region": "Region", "user_group": "Team"}
    lines = [f"Distribution across {n} reported cases:", ""]
    for k in ("os", "platform", "user_group", "region"):
        top = stats["dims"].get(k) or []
        if top:
            parts = ", ".join(f"{v} ({round(100 * c / n)}%)" for v, c in top)
            lines.append(f"- **{labels[k]}:** {parts}")
    return "\n".join(lines)


# ── resolution examples (coverage-picked) ────────────────────────────────────────
def _words(s: str) -> set:
    s = re.sub(r"<[a-z_]+>", " ", s.lower())
    s = re.sub(r"\d+(\.\d+)?", " ", s)
    s = re.sub(r"[^a-z ]", " ", s)
    return {w for w in s.split() if len(w) > 3}


def pick_resolution_examples(members: list[dict], k: int = 2):
    vocab: Counter = Counter()
    per = []
    for m in members:
        steps = _as_json(m.get("resolution_steps"), [])
        if not isinstance(steps, list) or not steps:
            continue
        w = set().union(*(_words(s) for s in steps))
        per.append((m["ticket_id"], steps, w))
        vocab.update(w)
    if not per:
        return []
    top = {w for w, _ in vocab.most_common(20)}
    per.sort(key=lambda x: len(x[2] & top), reverse=True)
    chosen: list = []
    seen: set = set()
    for tid, steps, w in per:
        if not chosen:
            chosen.append((tid, steps))
            seen = set(w)
        elif len(chosen) < k and len(w - seen) >= 3:
            chosen.append((tid, steps))
            seen |= w
        if len(chosen) >= k:
            break
    return chosen


def _steps_md(steps) -> str:
    out = []
    for i, s in enumerate(steps, 1):
        if isinstance(s, dict):
            exp = s.get("expected_result", "")
            out.append(f"{i}. {s.get('action', '')}" + (f"  \n   *Expected:* {exp}" if exp else ""))
        else:
            out.append(f"{i}. {s}")
    return "\n".join(out)


# ── page rendering ───────────────────────────────────────────────────────────────
def render_page(conn, row) -> tuple[str, int, str]:
    """Returns (title, self_serviceable, markdown) for one wiki_pages row."""
    fam, rc = row["family"], row["root_cause_id"]
    u = _as_json(row["curated_description"], {}) or {}
    curated = bool(row["curated_description"])
    diag = _as_json(row["diagnostic_steps"], [])

    members = [dict(m) for m in conn.execute(
        "SELECT ticket_id, environment, resolution_steps, root_cause_narrative "
        "FROM tickets WHERE root_cause_id = ? ORDER BY ticket_id", (rc,))]
    env = env_top3(members)
    examples = pick_resolution_examples(members, k=2)
    selfsvc = self_serviceable(rc, [m.get("root_cause_narrative") or "" for m in members])

    title = (u.get("title") or "").strip() or humanize(slug(rc))
    fm = {
        "root_cause_id": rc, "family": fam, "ticket_count": len(members),
        "curated": curated, "self_serviceable": bool(selfsvc),
    }
    front = ("---\nhide:\n  - navigation\n" + "".join(
        f"{k}: {json.dumps(v) if isinstance(v, (bool,)) else v}\n" for k, v in fm.items()
    ) + "---\n")

    p = [front, f"# {title}", "", "[← Back to categories](../../index.md)", ""]
    if not curated:
        p += ['!!! info "Curation pending"', "",
              "    The plain-language summary for this issue has not been generated yet. "
              "The affected environment and diagnostics below are drawn from the source tickets.", ""]

    if curated and (u.get("symptoms") or "").strip():
        p += ["## Description", "", u["symptoms"].strip(), ""]
        if (u.get("variations") or "").strip():
            p += ['!!! note "Reported variations"', "",
                  "    " + u["variations"].strip().replace("\n", "\n    "), ""]

    p += ["## Affected environment", "", _env_block(env), ""]

    if curated and (u.get("cause") or "").strip():
        p += ["## Root cause", "", u["cause"].strip(), ""]

    if diag:
        p += ["## Diagnostics", "", "Steps used to confirm this root cause:", "",
              _steps_md(diag), ""]

    if examples:
        p += ["## Resolution", ""]
        p += ["Representative resolutions from prior cases:" if selfsvc
              else "Performed by IT support. Representative resolutions from prior cases:", ""]
        for idx, (_tid, steps) in enumerate(examples, 1):
            if len(examples) > 1:
                p += [f"**Example {idx}**", ""]
            p += [_steps_md(steps), ""]

    if curated and (u.get("reporting") or "").strip():
        p += ["## Recommendation", "", u["reporting"].strip(), ""]

    p += ["---", "", "[← Back to categories](../../index.md)", ""]
    return title, selfsvc, "\n".join(p).rstrip() + "\n"


# ── home page + nav ──────────────────────────────────────────────────────────────
def build_index_and_nav(mkdocs_dir: Path, pages: list[tuple]) -> Path:
    """pages: list of (family, title, link, self_serviceable)."""
    fam_names = load_family_names()
    entries = defaultdict(list)
    for fam, title, link, ss in pages:
        entries[fam].append((title, link, ss))
    fams = sorted(entries, key=lambda f: str(fam_names.get(f, f)).lower())
    labels = [(fam_names.get(f, f), f) for f in fams]

    out = ["---", "hide:", "  - navigation", "---", "",
           "# ITSM Knowledge Wiki {.hero-title}", ""]
    out += ['<div class="category-pane" markdown="1">', "", "**Categories**", ""]
    for name, _ in labels:
        out.append(f"- [{name}](#{anchor(name)})")
    out += ["", "</div>", ""]
    for name, fam in labels:
        out += [f"## {name}", ""]
        for title, link, ss in sorted(entries[fam]):
            out.append(f"- [{title}]({link})" + (" · self-service" if ss else ""))
        out += ["", "[↑ Back to top](#itsm-knowledge-wiki)", ""]

    idx = mkdocs_dir / "docs" / "index.md"
    idx.write_text("\n".join(out).rstrip() + "\n", encoding="utf-8")
    _write_nav(mkdocs_dir, labels, entries)
    return idx


def _write_nav(mkdocs_dir: Path, labels, entries) -> None:
    mk = mkdocs_dir / "mkdocs.yml"
    text = mk.read_text(encoding="utf-8")
    cut = text.find("\nnav:")
    if cut != -1:
        text = text[:cut]
    text = text.rstrip() + "\n"
    lines = ["", "nav:"]
    for name, fam in labels:
        lines.append(f"  - {json.dumps(name)}:")
        for title, link, _ss in sorted(entries[fam]):
            lines.append(f"      - {json.dumps(title)}: {link}")
    mk.write_text(text + "\n".join(lines) + "\n", encoding="utf-8")


def render_all(conn, mkdocs_dir: Path) -> tuple[int, int]:
    out_wiki = mkdocs_dir / "docs" / "wiki"
    pages = []
    curated_n = 0
    for row in conn.execute("SELECT * FROM wiki_pages ORDER BY family, root_cause_id"):
        title, selfsvc, md = render_page(conn, row)
        fam, sl = row["family"], slug(row["root_cause_id"])
        (out_wiki / fam).mkdir(parents=True, exist_ok=True)
        (out_wiki / fam / f"{sl}.md").write_text(md, encoding="utf-8")
        pages.append((fam, title, f"wiki/{fam}/{sl}.md", selfsvc))
        if row["curated_description"]:
            curated_n += 1
    build_index_and_nav(mkdocs_dir, pages)
    return len(pages), curated_n


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db", type=Path, help="explicit DB path (default: settings.operational_store)")
    ap.add_argument("--mkdocs-dir", type=Path, default=DEFAULT_BUILD,
                    help="where to write generated pages (default: .mkdocs, ephemeral)")
    args = ap.parse_args()

    conn = get_connection(args.db)
    n, curated = render_all(conn, args.mkdocs_dir)
    conn.close()
    print(f"rendered {n} page(s) into {args.mkdocs_dir.name}/docs/wiki ({curated} curated, "
          f"{n - curated} curation-pending)")
    print(f"home + nav written. Preview:  mkdocs serve -f {args.mkdocs_dir.name}/mkdocs.yml")


if __name__ == "__main__":
    main()
