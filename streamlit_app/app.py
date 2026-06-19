"""
ITSM Ticket Search — main page.

Google-style interface: centered search box, 10 random tickets when idle,
LIKE search across description / correspondence / errors when a query is entered.
Result cards link to ticket_detail.py via query param (?id=) — true anchor links,
no session-state fragility.

DB resolution order:
  1. $OPERATIONAL_STORE/itsm_rag.db   (local dev / Docker, via .env)
  2. streamlit_app/data/itsm_rag.db   (Streamlit Cloud committed snapshot)
"""

import json
import os
import pathlib
import sqlite3

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="ITSM Ticket Search",
    page_icon=None,
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── CSS ───────────────────────────────────────────────────────────────────────

st.markdown(
    """
    <style>
      #MainMenu  { visibility: hidden; }
      footer     { visibility: hidden; }
      .block-container { padding-top: 4rem !important; }

      /* result card */
      .ticket-id      { font-size: 20px; font-weight: 600; color: #1a0dab; }
      .ticket-meta    { font-size: 15px; color: #006621; margin: 3px 0 6px 0; }
      .ticket-snippet { font-size: 15px; color: #3c4043; line-height: 1.55; }
      .view-link a    {
          display: inline-block;
          font-size: 14px;
          font-weight: 600;
          color: #1a0dab;
          text-decoration: none;
          padding: 4px 12px;
          border: 1px solid #dadce0;
          border-radius: 4px;
          margin-top: 6px;
      }
      .view-link a:hover { background: #f8f9fa; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── DB helper ─────────────────────────────────────────────────────────────────

def _db_path() -> pathlib.Path:
    env = os.getenv("OPERATIONAL_STORE")
    if env:
        return pathlib.Path(env) / "itsm_rag.db"
    return pathlib.Path(__file__).parent / "data" / "itsm_rag.db"


@st.cache_resource
def get_connection():
    path = _db_path()
    if not path.exists():
        st.error(
            f"Database not found at `{path}`.  \n"
            "Run `uv run sh scripts/run_ingest.sh` first, "
            "or set `OPERATIONAL_STORE` in `.env`."
        )
        st.stop()
    return sqlite3.connect(str(path), check_same_thread=False)


# ── Header ────────────────────────────────────────────────────────────────────

st.markdown(
    "<h1 style='text-align:center;letter-spacing:-1px;margin-bottom:4px'>"
    "ITSM Ticket Search</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='text-align:center;color:#5f6368;font-size:16px;margin-top:0'>"
    "745 redacted IT support tickets · synthetic corpus</p>",
    unsafe_allow_html=True,
)
st.markdown("<br>", unsafe_allow_html=True)

# ── Search box ────────────────────────────────────────────────────────────────

query = st.text_input(
    label="search",
    placeholder="Search by symptom, error code, application, or root cause…",
    label_visibility="collapsed",
)

# ── Family filter ─────────────────────────────────────────────────────────────

con = get_connection()
families = [
    r[0]
    for r in con.execute(
        "SELECT DISTINCT family FROM tickets ORDER BY family"
    ).fetchall()
]

with st.sidebar:
    st.markdown("### Filter by family")
    selected_family = st.selectbox("Family", ["All"] + families)

# ── Query ─────────────────────────────────────────────────────────────────────

family_clause = "" if selected_family == "All" else "AND family = :family"

if query.strip():
    like = f"%{query.strip()}%"
    sql = f"""
        SELECT ticket_id, family, priority, root_cause_id,
               submitted_description, observed_errors
        FROM   tickets
        WHERE  (
                   submitted_description LIKE :like
                OR correspondence        LIKE :like
                OR observed_errors       LIKE :like
                OR root_cause_narrative  LIKE :like
               )
               {family_clause}
        ORDER  BY ticket_id
        LIMIT  20
    """
    rows = con.execute(sql, {"like": like, "family": selected_family}).fetchall()
    n = len(rows)
    label = f"{n} result{'s' if n != 1 else ''} for \"{query}\""
    if selected_family != "All":
        label += f" · family {selected_family}"
else:
    # Seed random per session so the same 10 tickets stay stable across reruns
    # (prevents cards shuffling on every button interaction).
    if "rand_seed" not in st.session_state:
        import random
        st.session_state["rand_seed"] = random.randint(0, 999999)
    sql = f"""
        SELECT ticket_id, family, priority, root_cause_id,
               submitted_description, observed_errors
        FROM   tickets
        WHERE  1=1 {family_clause}
        ORDER  BY substr(ticket_id || :seed, 1, 999)
        LIMIT  10
    """
    rows = con.execute(sql, {
        "seed":   str(st.session_state["rand_seed"]),
        "family": selected_family,
    }).fetchall()
    label = "Showing 10 tickets — type to search"
    if selected_family != "All":
        label += f" · family {selected_family}"

st.caption(label)
st.markdown("<br>", unsafe_allow_html=True)

# ── Results ───────────────────────────────────────────────────────────────────

if not rows:
    st.info("No tickets match your search.")

for ticket_id, family, priority, root_cause_id, description, errors_raw in rows:

    try:
        errors = json.loads(errors_raw or "[]")
        error_hint = errors[0] if errors else ""
    except (json.JSONDecodeError, TypeError):
        error_hint = ""

    snippet = (description or "")[:240].rstrip()
    if len(description or "") > 240:
        snippet += "…"

    badge_colour = {
        "critical": "#d93025",
        "high":     "#e37400",
        "medium":   "#1e8e3e",
        "low":      "#5f6368",
    }.get((priority or "").lower(), "#5f6368")

    short_root = (root_cause_id or "").split("/")[-1]

    with st.container(border=True):
        # Title row
        st.markdown(
            f"<div class='ticket-id'>{ticket_id}</div>",
            unsafe_allow_html=True,
        )
        # Metadata row
        st.markdown(
            f"<div class='ticket-meta'>"
            f"Family: <b>{family}</b> &nbsp;·&nbsp; "
            f"<span style='color:{badge_colour}'><b>{(priority or '').capitalize()}</b></span>"
            f"&nbsp;·&nbsp; {short_root}"
            f"{'&nbsp;·&nbsp; <i>' + error_hint + '</i>' if error_hint else ''}"
            f"</div>",
            unsafe_allow_html=True,
        )
        # Snippet
        st.markdown(
            f"<div class='ticket-snippet'>{snippet}</div>",
            unsafe_allow_html=True,
        )
        # Link — true anchor, no session-state fragility
        st.markdown(
            f"<div class='view-link'>"
            f"<a href='/ticket_detail?id={ticket_id}' target='_self'>View ticket →</a>"
            f"</div>",
            unsafe_allow_html=True,
        )
