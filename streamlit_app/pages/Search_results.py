"""
Search results — live L1 retrieval.

A query is embedded (dense Arctic + sparse BM25) and fused with Reciprocal Rank Fusion in
Qdrant. The top section points come back as (ticket, section) pairs and render as cards with
the excerpt from that section. The faceted filters (family, priority, SLA tier, region,
application) are built from the retrieved results and narrow them — they never show the whole
corpus. Each result links to the ticket detail view.

Needs a built index: Qdrant up (or embedded) and scripts/build_retrieval_index.sh run. See
docs/running.md. Ticket display fields are read from the SQLite operational store.
"""

import json
import os
import pathlib
import sys
import urllib.parse

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# src/ on path so the app can import the retriever package.
_REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO / "src"))

# ── section contract (mirrors corpus/sections.py) ──────────────────────────────
SECTION_COLUMNS = {
    "description": "submitted_description",
    "correspondence": "correspondence",
    "diagnostics": "diagnostics_procedure",
    "resolution": "resolution_steps",
}
SECTION_NAMES = tuple(SECTION_COLUMNS)

POOL = 100         # candidates retrieved per query — covers most of the relevant distribution
PER_PAGE = 10      # results per page; the retrieved set is paginated client-side
# The dense-cosine relevance floor that gates results is app functionality, not a UI constant:
# it lives in src/retrieval/relevance.py (relevant_keys) and config.settings.cosine_relevance_floor.


def render_section(value) -> str:
    if value is None:
        return ""
    s = str(value)
    if s[:1] in "[{":
        try:
            obj = json.loads(s)
        except json.JSONDecodeError:
            return s
        if isinstance(obj, list):
            return "\n".join(render_section(x) for x in obj)
        if isinstance(obj, dict):
            return "; ".join(f"{k}: {v}" for k, v in obj.items())
    return s


def sla_tier(s: str) -> str:
    """Normalize the free-text sla_plan into a small set of tiers."""
    s = (s or "").lower()
    for key in ("gold", "enterprise", "tier", "internal", "business", "standard"):
        if key in s:
            return "Tier" if key == "tier" else key.capitalize()
    return "Other"


@st.cache_data
def family_labels() -> dict:
    p = pathlib.Path(__file__).parent.parent / "family_names.json"
    try:
        return {k: v for k, v in json.loads(p.read_text()).items() if not k.startswith("_")}
    except Exception:
        return {}


LABELS = family_labels()


def fam_label(code: str) -> str:
    return f"{code} — {LABELS[code]}" if code in LABELS else code


# ── page config + CSS ──────────────────────────────────────────────────────────
st.set_page_config(page_title="Search results", layout="centered",
                   initial_sidebar_state="expanded")
st.markdown(
    """
    <style>
      #MainMenu { visibility: hidden; } footer { visibility: hidden; }
      .block-container { padding-top: 3rem !important; }
      .ticket-id   { font-size: 20px; font-weight: 600; color: #1a0dab; }
      .ticket-id a { color: inherit; text-decoration: none; }
      .ticket-id a:hover { text-decoration: underline; }
      .ticket-meta { font-size: 15px; color: #006621; margin: 3px 0 4px 0; }
      .sec-badge   { display:inline-block; font-size:12px; font-weight:600; color:#3c4043;
                     background:#eef1f5; border:1px solid #dadce0; border-radius:10px;
                     padding:1px 9px; margin: 2px 0 6px 0; text-transform:uppercase;
                     letter-spacing:.4px; }
      .err-line    { font-size:13px; color:#b3261e; margin: 0 0 4px 0; }
      .ctx-line    { font-size:12.5px; color:#5f6368; margin: 0 0 6px 0; }
      .ticket-snippet { font-size: 15px; color: #3c4043; line-height: 1.55; }
      .view-link a { display:inline-block; font-size:14px; font-weight:600; color:#1a0dab;
                     text-decoration:none; padding:4px 12px; border:1px solid #dadce0;
                     border-radius:4px; margin-top:6px; }
      .view-link a:hover { background:#f8f9fa; }
    </style>
    """,
    unsafe_allow_html=True,
)


def _db_path() -> pathlib.Path:
    env = os.getenv("OPERATIONAL_STORE")
    if env:
        return pathlib.Path(env) / "itsm_rag.db"
    return pathlib.Path(__file__).parent.parent / "data" / "itsm_rag.db"


@st.cache_data
def load_section_cards() -> list[dict]:
    import sqlite3
    path = _db_path()
    if not path.exists():
        st.error(f"Database not found at `{path}`. Run `uv run sh scripts/run_ingest.sh` first.")
        st.stop()
    con = sqlite3.connect(str(path))
    cols = ", ".join(SECTION_COLUMNS[s] for s in SECTION_NAMES)
    rows = con.execute(
        f"SELECT ticket_id, family, priority, root_cause_id, observed_errors, applications, "
        f"environment, sla_plan, {cols} FROM tickets").fetchall()
    con.close()
    out = []
    for r in rows:
        tid, family, priority, rc, errs_raw, apps_raw, env_raw, sla, *secs = r
        try:
            errs = json.loads(errs_raw or "[]")
        except (json.JSONDecodeError, TypeError):
            errs = []
        env = json.loads(env_raw or "{}") or {}
        base = {
            "tid": tid, "family": family, "priority": priority,
            "root_cause": (rc or "").split("/")[-1], "errors": errs,
            "apps": json.loads(apps_raw or "[]"),
            "region": env.get("region"), "platform": env.get("platform"),
            "user_group": env.get("user_group"), "os": env.get("os"),
            "sla": sla, "sla_tier": sla_tier(sla),
        }
        for name, raw in zip(SECTION_NAMES, secs):
            text = render_section(raw).strip()
            if text:
                out.append({**base, "section": name, "text": text})
    return out


CARDS = load_section_cards()
LOOKUP = {(c["tid"], c["section"]): c for c in CARDS}


@st.cache_resource(show_spinner="Loading the retriever (first run downloads the embedding model)…")
def get_retriever():
    """Build the arms once per app process. Returns the {name: arm} dict, or an error string."""
    try:
        from retrieval import build_arms
        return build_arms()
    except Exception as exc:  # noqa: BLE001 — surfaced to the user below
        return repr(exc)


class _Query:
    """Minimal shape the retriever needs (it only reads .text)."""

    def __init__(self, text: str) -> None:
        self.text = text
        self.query_id = "ui"


# Faceted filters. Each option set is computed from the retrieved results, not the corpus.
SCALARS = [("family", "Family"), ("priority", "Priority"), ("sla_tier", "SLA tier"),
           ("region", "Region")]   # + Application multiselect


def facet_values(cards, dim):
    """Distinct values of one facet across the retrieved cards."""
    if dim == "apps":
        return sorted({a for c in cards for a in c["apps"]})
    return sorted({c[dim] for c in cards if c[dim]})


def passes(card, sel):
    for dim, _ in SCALARS:
        if sel[dim] != "All" and card[dim] != sel[dim]:
            return False
    if sel["apps"] and not (set(sel["apps"]) & set(card["apps"])):
        return False
    return True


# ── header + search ─────────────────────────────────────────────────────────────
# Clickable wordmark — returns to the Home landing page (the / root), like Google's logo.
st.markdown(
    "<div style='text-align:center;margin-bottom:2px'>"
    "<a href='/' target='_self' title='Back to home' "
    "style='text-decoration:none;font-weight:700;font-size:30px;letter-spacing:-1px'>"
    "<span style='color:#4285f4'>I</span><span style='color:#ea4335'>T</span>"
    "<span style='color:#fbbc05'>S</span><span style='color:#4285f4'>M</span>"
    "<span style='color:#34a853'>&nbsp;Knowledge</span>"
    "<span style='color:#ea4335'>&nbsp;Search</span></a></div>",
    unsafe_allow_html=True)
st.markdown("<p style='text-align:center;color:#5f6368;margin-top:0'>"
            "Live hybrid retrieval across the ticket corpus</p>",
            unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)
# Seed the box from the URL (?q=) so a ticket-detail round-trip — a hard navigation that
# resets session state — returns to the same results. The box is the source of truth after.
if "sec_q" not in st.session_state and st.query_params.get("q"):
    st.session_state["sec_q"] = st.query_params.get("q")
query = st.text_input("search", placeholder="Search section text, error code, application…",
                      label_visibility="collapsed", key="sec_q").strip()
if query and st.query_params.get("q") != query:
    st.query_params["q"] = query        # mirror to the URL so results are shareable + navigable

# ── retrieve a candidate pool (the universe for both facets and results) ─────────
candidates: list[dict] = []
retriever_error = None
if query:
    arms = get_retriever()
    if not isinstance(arms, dict):
        retriever_error = arms
    else:
        from retrieval.relevance import relevant_keys   # app-level gate (hybrid rank + cosine floor)
        q = _Query(query)
        for key in relevant_keys(arms, q, POOL):
            if key in LOOKUP:
                candidates.append(LOOKUP[key])

# ── sidebar facets, built from the retrieved candidates ───────────────────────────
with st.sidebar:
    st.markdown("### Filters")
    st.caption("Options reflect the current results.")
    widgets = {}
    for dim, label in SCALARS:
        opts = ["All"] + facet_values(candidates, dim)
        key = f"f_{dim}"
        if st.session_state.get(key, "All") not in opts:   # drop a stale selection
            st.session_state[key] = "All"
        fmt = (lambda c: "All" if c == "All" else fam_label(c)) if dim == "family" else None
        widgets[dim] = (st.selectbox(label, opts, key=key, format_func=fmt) if fmt
                        else st.selectbox(label, opts, key=key))
    app_opts = facet_values(candidates, "apps")
    st.session_state["f_apps"] = [a for a in st.session_state.get("f_apps", []) if a in app_opts]
    widgets["apps"] = st.multiselect("Application", app_opts, key="f_apps")

sel = {dim: widgets[dim] for dim, _ in SCALARS}
sel["apps"] = widgets["apps"]

# ── results ───────────────────────────────────────────────────────────────────────
if retriever_error is not None:
    st.error(
        "Live retrieval is not available. Build the index first "
        "(`uv run sh scripts/build_retrieval_index.sh`). See docs/running.md."
        f"\n\nDetail: {retriever_error}")
    st.stop()

shown: list[dict] = []
n_pages, page = 1, 0
if not query:
    st.caption("Type a query to retrieve the most relevant ticket sections.")
else:
    filtered = [c for c in candidates if passes(c, sel)]
    # Reset to the first page whenever the query or the active filters change.
    sig = (query, tuple(sel[d] for d, _ in SCALARS), tuple(sorted(sel["apps"])))
    if st.session_state.get("res_sig") != sig:
        st.session_state["res_sig"] = sig
        st.session_state["page"] = 0
    n_pages = max(1, (len(filtered) + PER_PAGE - 1) // PER_PAGE)
    page = min(st.session_state.get("page", 0), n_pages - 1)
    shown = filtered[page * PER_PAGE: page * PER_PAGE + PER_PAGE]
    active = [f"{label}: {sel[dim]}" for dim, label in SCALARS if sel[dim] != "All"]
    if sel["apps"]:
        active.append("Application: " + ", ".join(sel["apps"]))
    filter_str = ("  ·  " + " · ".join(active)) if active else ""
    st.caption(f"{len(filtered)} result{'s' if len(filtered) != 1 else ''} for \"{query}\"  ·  "
               f"page {page + 1} of {n_pages}{filter_str}")

st.markdown("<br>", unsafe_allow_html=True)
if query and not shown:
    st.info("No retrieved section matches these filters.")

q_param = urllib.parse.quote(query)   # carried on ticket links so "back" returns here
badge_colour = {"critical": "#d93025", "high": "#e37400", "medium": "#1e8e3e", "low": "#5f6368"}
for c in shown:
    snippet = c["text"][:260].rstrip() + ("…" if len(c["text"]) > 260 else "")
    colour = badge_colour.get((c["priority"] or "").lower(), "#5f6368")
    err_line = " · ".join(c["errors"]) if c["errors"] else ""
    ctx = " · ".join(x for x in [f"SLA: {c['sla']}" if c["sla"] else None, c["region"]] if x)
    with st.container(border=True):
        st.markdown(
            f"<div class='ticket-id'><a href='/ticket_detail?id={c['tid']}&q={q_param}' "
            f"target='_self'>{c['tid']}</a></div>", unsafe_allow_html=True)
        st.markdown(
            f"<div class='ticket-meta'>{fam_label(c['family'])} &nbsp;·&nbsp; "
            f"<span style='color:{colour}'><b>{(c['priority'] or '').capitalize()}</b></span>"
            f"&nbsp;·&nbsp; {c['root_cause']}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='sec-badge'>{c['section']}</div>", unsafe_allow_html=True)
        if err_line:
            st.markdown(f"<div class='err-line'>⚠ {err_line}</div>", unsafe_allow_html=True)
        if ctx:
            st.markdown(f"<div class='ctx-line'>{ctx}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='ticket-snippet'>{snippet}</div>", unsafe_allow_html=True)
        st.markdown(
            f"<div class='view-link'><a href='/ticket_detail?id={c['tid']}&q={q_param}' "
            f"target='_self'>View ticket →</a></div>", unsafe_allow_html=True)

# ── pagination (up to 10 page links) ──────────────────────────────────────────────
if query and n_pages > 1:
    st.markdown("<br>", unsafe_allow_html=True)
    nav = st.columns(n_pages)
    for i in range(n_pages):
        if nav[i].button(str(i + 1), key=f"pg_{i}", disabled=(i == page),
                         use_container_width=True):
            st.session_state["page"] = i
            st.rerun()
