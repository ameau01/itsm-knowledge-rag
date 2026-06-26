"""Query-time L2 selection — pick the one overview page an L1 result ties to.

* Collapses an L1 result (a rank-ordered distribution over root causes) to one L2 page and reads its cached overview
* Filter-agnostic: the caller passes the UNFILTERED gated candidates.
      SELECTION STRATEGY = vote + guardrail ("vote_guard"), 
* Chosen by calibration on the fixed corpus (97 labelled eval-set queries):
    vote_guard 0.773  >  top1 0.753  >  vote 0.649     (top-1 selection accuracy vs gold root cause)
* Pure vote alone is size-biased. The guardrail — defer to the rank-1 chunk's root cause.
 when the vote winner doesn't own a top-2 key — fixes that and beats top-1.

* CONFIDENCE = the page's STATIC tier (ticket-count based), unchanged by the query. 
* Calibration showed it barely predicts accuracy (margin≈0 "ambiguous" 0.75 vs margin>0 "clean" 0.785).
** margin is used only as a binary `ambiguous` flag to surface the runner-up and soften framing.

"""

from __future__ import annotations

from dataclasses import dataclass

RRF_K = 60                 # rank-decay constant, matching RRF convention
AMBIGUOUS_MARGIN = 0.0     # margin <= this -> ambiguous (guardrail override; vote/rank disagree)

_TIERS = ["high", "medium", "low"]


def reconstruct_rc(family: str | None, slug: str | None) -> str | None:
    """Full root_cause_id from a card's family + root cause-slug. Return None if either is missing. unclassified tickets must not pollute the vote)."""
    if not family or not slug:
        return None
    return f"{family}/{slug}"


def tally(ranked_rcs: list[str | None], k: int = RRF_K) -> dict[str, float]:
    """Rank-weighted vote: each candidate contributes 1/(k+rank), rank = position. Empty/None skip. All section types vote equally."""
    scores: dict[str, float] = {}
    for rank, rc in enumerate(ranked_rcs):
        if not rc:
            continue
        scores[rc] = scores.get(rc, 0.0) + 1.0 / (k + rank)
    return scores


def pick_winner(scores: dict[str, float], ranked_rcs: list[str | None]) -> tuple[str | None, float]:
    """(winner, margin). Guardrail: the winner must own the top-2 ranked keys, else defer to the rank-1 key's root cause; else margin = (s1-s2)/s1."""
    if not scores:
        return None, 0.0
    ordered = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    winner, s1 = ordered[0]
    s2 = ordered[1][1] if len(ordered) > 1 else 0.0

    top2 = [rc for rc in ranked_rcs if rc][:2]
    if winner not in top2:
        fallback = next((rc for rc in ranked_rcs if rc), None)
        if fallback is not None and fallback != winner:
            return fallback, 0.0

    margin = (s1 - s2) / s1 if s1 > 0 else 0.0
    return winner, round(max(0.0, margin), 4)


@dataclass
class Selection:
    root_cause_id: str
    family: str
    ai_overview: dict
    curated_description: dict | None = None
    diagnostic_steps: object = None
    selection_margin: float = 0.0
    confidence: str = "low"
    ambiguous: bool = False
    runner_up: str | None = None


def select_overview(ranked_keys, lookup, conn, *, k: int = RRF_K,
                    ambiguous_margin: float = AMBIGUOUS_MARGIN, get_ai_overview=None) -> Selection | None:
    """Pick the L2 page for an L1 result and return its overview, or None.

    ranked_keys : rank-ordered (ticket_id, section_name) from relevance.relevant_keys
    lookup      : (ticket_id, section_name) -> card with 'family' + 'root_cause'
    conn        : operational store connection.
    Returns None on: empty L1 (abstain), no usable winner, or a NULL/missing overview cell.
    """
    if not ranked_keys:
        return None
    ranked_rcs = []
    for key in ranked_keys:
        card = lookup.get(key) if lookup else None
        ranked_rcs.append(reconstruct_rc(card.get("family"), card.get("root_cause"))
                          if card else None)

    scores = tally(ranked_rcs, k=k)
    winner, margin = pick_winner(scores, ranked_rcs)
    if winner is None:
        return None

    if get_ai_overview is None:
        from operational_store.store import get_ai_overview as get_ai_overview
    page = get_ai_overview(conn, winner)
    if page is None:                 # NULL cell / missing column / no row -> show nothing
        return None

    stored = (page["ai_overview"] or {}).get("confidence", "low")
    stored = stored if stored in _TIERS else "low"
    # In an override (ambiguous), the winner is the rank-1
    ordered = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    runner_up = next((rc for rc, _ in ordered if rc != winner), None)
    return Selection(
        root_cause_id=winner, family=page["family"], ai_overview=page["ai_overview"],
        curated_description=page.get("curated_description"),
        diagnostic_steps=page.get("diagnostic_steps"),
        selection_margin=margin, confidence=stored,
        ambiguous=(margin <= ambiguous_margin), runner_up=runner_up,
    )
