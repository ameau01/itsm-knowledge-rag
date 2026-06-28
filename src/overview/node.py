"""The overview node — orchestration. Reads pages, computes confidence, calls the agent, writes back.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from overview import agent as agentmod
from overview.confidence import confidence_tier, root_cause_nature, ticket_count

from operational_store.store import update_wiki_overview

PIPELINE_VERSION = "overview-v1"

# Guarded LangSmith import: no-op decorator when langsmith is absent, so the code runs identically
# with or without tracing installed.
try:
    from langsmith import traceable
except ImportError:  # pragma: no cover
    def traceable(*a, **k):
        return a[0] if a and callable(a[0]) else (lambda f: f)


def assemble_overview(gen: dict, n_tickets: int, nature: str) -> dict:
    """Wrap the generated lead/key_points with the deterministic confidence + evidence."""
    return {
        "lead": gen["lead"], "key_points": gen["key_points"],
        "confidence": confidence_tier(n_tickets, nature),
        "evidence": {"ticket_count": n_tickets, "root_cause_nature": nature},
    }


def assemble_details(model_label: str) -> dict:
    return {"model": model_label, "pipeline_version": PIPELINE_VERSION,
            "generated_at": datetime.now(timezone.utc).isoformat()}


@traceable(name="overview_page", run_type="chain")
def run_page(page: dict, *, agent=None, mock: bool = False, dry_run: bool = False) -> dict:
    """Generate one page's overview. Returns a result dict; does NOT touch the DB (the batch driver
    writes). page = {family, root_cause_id, curated_description (json str), curated_tickets}."""
    rc, fam = page["root_cause_id"], page["family"]
    cd = page["curated_description"]
    if isinstance(cd, str):
        cd = json.loads(cd)
    n = ticket_count(page.get("curated_tickets"))
    nature = root_cause_nature(rc)
    tier = confidence_tier(n, nature)

    if dry_run:
        system, user = agentmod.build_prompt(cd, tier)
        return {"root_cause_id": rc, "family": fam, "confidence": tier,
                "ticket_count": n, "nature": nature, "system": system, "user": user}

    if mock:
        gen, model_label = agentmod.mock_generate(cd, tier), "MOCK"
    else:
        gen, model_label = agent.generate(cd, tier), agent.label

    return {"root_cause_id": rc, "family": fam, "confidence": tier,
            "ticket_count": n, "nature": nature,
            "ai_overview": assemble_overview(gen, n, nature),
            "details": assemble_details(model_label)}


def run_batch(conn, pages: list[dict], *, agent=None, mock: bool = False,
              dry_run: bool = False) -> dict:
    """Read→generate→write across pages. Per-page failures isolated."""
    ok = fail = 0
    for i, page in enumerate(pages, 1):
        rc = page["root_cause_id"]
        try:
            res = run_page(page, agent=agent, mock=mock, dry_run=dry_run)
            if dry_run:
                print(f"[{i}/{len(pages)}] {rc}  (n={res['ticket_count']}, {res['nature']}, "
                      f"conf={res['confidence']})")
                if i == 1:
                    print("--- system ---\n" + res["system"]
                          + "\n--- user (first 900 chars) ---\n" + res["user"][:900])
                continue
            n = update_wiki_overview(
                conn, res["family"], rc,
                json.dumps(res["ai_overview"], ensure_ascii=False),
                json.dumps(res["details"], ensure_ascii=False))
            ok += 1
            kp = len(res["ai_overview"]["key_points"])
            print(f"[{i}/{len(pages)}] {rc}  conf={res['confidence']}  "
                  f"({kp} pts, store={'ok' if n else 'NO ROW'})")
        except Exception as e:  # noqa: BLE001 — isolate per-page failures
            fail += 1
            print(f"[{i}/{len(pages)}] {rc}  — ERROR: {e}")
    return {"ok": ok, "fail": fail, "n": len(pages)}


# --------------------------------------------------------------------------- #
# Verify (read back + check) — QA on the stored overviews.
# --------------------------------------------------------------------------- #
def verify(conn) -> int:
    import re
    rows = conn.execute(
        "SELECT family, root_cause_id, curated_tickets, ai_overview FROM wiki_pages "
        "WHERE ai_overview IS NOT NULL AND ai_overview <> ''"
    ).fetchall()
    if not rows:
        print("verify: no ai_overview rows yet.")
        return 0
    problems = 0
    tiers = {"high": 0, "medium": 0, "low": 0}
    for r in rows:
        rc = r["root_cause_id"]
        try:
            o = json.loads(r["ai_overview"])
        except json.JSONDecodeError:
            print(f"  BAD JSON: {rc}")
            problems += 1
            continue
        lead = o.get("lead", "")
        kps = o.get("key_points", [])
        conf = o.get("confidence")
        ev = o.get("evidence", {})
        n = ticket_count(r["curated_tickets"])
        nature = root_cause_nature(rc)
        expect = confidence_tier(n, nature)
        tiers[conf] = tiers.get(conf, 0) + 1
        core = re.sub(r"^(Based on[^:]*:\s*|Likely cause:\s*)", "", lead)
        if len(core) > 230:
            print(f"  LONG lead ({len(core)}c): {rc}")
            problems += 1
        if not (1 <= len(kps) <= 5):
            print(f"  key_points={len(kps)} (want 1-5): {rc}")
            problems += 1
        if conf != expect:
            print(f"  CONFIDENCE {conf}!=expected {expect} (n={n},{nature}): {rc}")
            problems += 1
        if nature == "unconfirmed" and conf != "low":
            print(f"  LOW-TRUST not forced low: {rc}")
            problems += 1
        if ev.get("ticket_count") != n:
            print(f"  evidence count {ev.get('ticket_count')}!={n}: {rc}")
            problems += 1
    print(f"verify: {len(rows)} overview(s) | tiers {tiers} | {problems} problem(s)")
    return problems
