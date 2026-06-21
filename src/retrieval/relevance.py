"""
Serve-time relevance gate.

Hybrid RRF decides the ranking. Dense cosine decides whether each ranked section is relevant
enough to return. A section whose dense cosine falls below the floor is dropped. So a weak or
off-topic query returns fewer results, or none, instead of padding to the pool size.

This is app functionality, not a UI detail. The gate and its floor live here so the Streamlit
app and any other caller apply the same rule. The floor is configured once in
config.settings.cosine_relevance_floor. It is the per-result cutoff. It is distinct from the
abstention floor, which is derived from the in-corpus score distribution and decides whether the
whole query has any answer at all.
"""

from __future__ import annotations

from config import settings


def relevant_keys(arms, query, pool, floor=None):
    """Hybrid-ranked (ticket_id, section_name) keys whose dense cosine clears the floor.

    arms  : {name: retriever} from retrieval.build_arms()
    query : an object exposing .text (the search string)
    pool  : candidates to fetch from each arm before gating
    floor : dense cosine cutoff; defaults to settings.cosine_relevance_floor

    The returned order follows the hybrid ranking. Sections below the floor are omitted, so the
    result count varies with query quality and can be empty.
    """
    cutoff = settings.cosine_relevance_floor if floor is None else floor
    ranked = arms["hybrid"].retrieve_points(query, pool)
    cosine = {(p.ticket_id, p.section_name): p.score
              for p in arms["dense"].retrieve_points(query, pool)}
    return [(p.ticket_id, p.section_name)
            for p in ranked
            if cosine.get((p.ticket_id, p.section_name), 0.0) >= cutoff]
