"""
Ticket detail page.

Reads ticket_id from:
  1. st.query_params["id"]          — URL: /ticket_detail?id=INC-VDA-0001
  2. st.session_state["ticket_id"]  — fallback for programmatic nav

Layout order:
  header → description (full-width) → environment tiles → correspondence turns
  → root cause → diagnostics → resolution
"""

import json
import os
import pathlib
import sqlite3
import urllib.parse

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Ticket Detail — ITSM",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS ───────────────────────────────────────────────────────────────────────

st.markdown(
    """
    <style>
      #MainMenu { visibility: hidden; }
      footer    { visibility: hidden; }
      .block-container { padding-top: 2rem !important; }

      /* base prose size — does NOT use !important so explicit sizes win */
      .block-container p,
      .block-container li { font-size: 16px; line-height: 1.6; }

      /* ticket ID — very large, explicit */
      .ticket-id-heading {
          font-size: 42px !important;
          font-weight: 800 !important;
          letter-spacing: -1.5px;
          color: #202124;
          margin: 0 0 12px 0;
          line-height: 1;
      }

      /* shared row style for header metadata + environment */
      .meta-row {
          display: flex;
          align-items: center;
          padding: 10px 16px;
          border-radius: 6px;
          margin-bottom: 4px;
      }
      .meta-row-odd  { background: #f1f3f4; }
      .meta-row-even { background: #ffffff; }
      .meta-label {
          font-size: 11px;
          font-weight: 700;
          text-transform: uppercase;
          letter-spacing: .07em;
          color: #80868b;
          min-width: 140px;
          flex-shrink: 0;
      }
      .meta-value {
          font-size: 16px;
          color: #202124;
          font-weight: 500;
      }

      /* conversation turns */
      .turn {
          padding: 12px 16px;
          border-radius: 8px;
          margin-bottom: 10px;
          font-size: 15px;
          line-height: 1.6;
      }
      .turn-odd  { background: #f1f3f4; }
      .turn-even { background: #e8f0fe; }

      .step-num {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          width: 24px; height: 24px;
          border-radius: 50%;
          background: #1a0dab;
          color: white;
          font-size: 12px !important;
          font-weight: 700;
          margin-right: 10px;
          flex-shrink: 0;
      }
      .step-row {
          display: flex;
          align-items: flex-start;
          margin-bottom: 12px;
          font-size: 15px !important;
          line-height: 1.55;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── DB helper ─────────────────────────────────────────────────────────────────

def _db_path() -> pathlib.Path:
    env = os.getenv("OPERATIONAL_STORE")
    if env:
        return pathlib.Path(env) / "itsm_rag.db"
    return pathlib.Path(__file__).parent.parent / "data" / "itsm_rag.db"


@st.cache_resource
def get_connection():
    path = _db_path()
    if not path.exists():
        st.error(f"Database not found at `{path}`.")
        st.stop()
    return sqlite3.connect(str(path), check_same_thread=False)


def load_ticket(ticket_id: str) -> dict | None:
    con = get_connection()
    cur = con.execute("SELECT * FROM tickets WHERE ticket_id = ?", (ticket_id,))
    row = cur.fetchone()
    if row is None:
        return None
    cols = [d[0] for d in cur.description]
    return dict(zip(cols, row))


def _json(value, fallback=None):
    if not value:
        return fallback if fallback is not None else []
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return fallback if fallback is not None else []

# ── Resolve ticket ID ─────────────────────────────────────────────────────────

ticket_id = st.query_params.get("id") or st.session_state.get("ticket_id")

# ── Back button ───────────────────────────────────────────────────────────────

_back_q = st.query_params.get("q", "")
_back_href = "/Search_results" + (f"?q={urllib.parse.quote(_back_q)}" if _back_q else "")
st.markdown(
    f"<a href='{_back_href}' target='_self' style='display:inline-block;font-size:14px;"
    f"font-weight:600;color:#1a0dab;text-decoration:none;padding:4px 12px;"
    f"border:1px solid #dadce0;border-radius:4px'>← Back to results</a>",
    unsafe_allow_html=True)

if not ticket_id:
    st.warning("No ticket selected. Return to search and click **View ticket →**.")
    st.stop()

ticket = load_ticket(ticket_id)
if ticket is None:
    st.error(f"Ticket `{ticket_id}` not found.")
    st.stop()

# ── Parse fields ──────────────────────────────────────────────────────────────

environment  = _json(ticket["environment"], {})
applications = _json(ticket["applications"], [])
diag_steps   = _json(ticket["diagnostics_procedure"], [])
res_steps    = _json(ticket["resolution_steps"], [])
errors       = _json(ticket["observed_errors"], [])

priority  = (ticket["priority"] or "").capitalize()
family    = ticket["family"] or ""
root_cause = (ticket["root_cause_id"] or "").split("/")[-1]

badge_colour = {
    "Critical": "#d93025",
    "High":     "#e37400",
    "Medium":   "#1e8e3e",
    "Low":      "#5f6368",
}.get(priority, "#5f6368")

# ── 1. Header ─────────────────────────────────────────────────────────────────

st.markdown(
    f"<div class='ticket-id-heading'>{ticket['ticket_id']}</div>",
    unsafe_allow_html=True,
)

# Priority badge value — rendered inline with the row
priority_badge = (
    f"<span style='background:{badge_colour};color:white;"
    f"padding:3px 14px;border-radius:12px;font-size:15px;font-weight:700'>"
    f"{priority}</span>"
)

header_rows = [
    ("Priority",   priority_badge),
    ("Family",     f"<b>{family}</b>"),
    ("Root Cause", root_cause),
    ("Submitted",  (ticket["submitted_at"] or "")[:10]),
]

for i, (label, value) in enumerate(header_rows):
    bg_class = "meta-row-odd" if i % 2 == 0 else "meta-row-even"
    st.markdown(
        f"<div class='meta-row {bg_class}'>"
        f"<span class='meta-label'>{label}</span>"
        f"<span class='meta-value'>{value}</span>"
        f"</div>",
        unsafe_allow_html=True,
    )

st.markdown("---")

# ── 2. Description (full width) ───────────────────────────────────────────────

st.markdown("#### Description")
st.markdown(
    f"<div style='background:#f8f9fa;padding:16px 20px;"
    f"border-radius:8px;font-size:16px;line-height:1.65'>"
    f"{ticket['submitted_description'] or '—'}"
    f"</div>",
    unsafe_allow_html=True,
)

st.markdown("<br>", unsafe_allow_html=True)

# ── 3. Environment (horizontal rows, like correspondence) ─────────────────────

st.markdown("#### Environment")

env_rows = list(environment.items())
if applications:
    env_rows.append(("applications", ", ".join(applications)))
if ticket["sla_plan"]:
    env_rows.append(("sla", ticket["sla_plan"]))

for i, (key, val) in enumerate(env_rows):
    bg_class = "meta-row-odd" if i % 2 == 0 else "meta-row-even"
    st.markdown(
        f"<div class='meta-row {bg_class}'>"
        f"<span class='meta-label'>{key}</span>"
        f"<span class='meta-value'>{val}</span>"
        f"</div>",
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)

# ── 4. Correspondence turns ───────────────────────────────────────────────────

raw_corr = (ticket["correspondence"] or "").strip()
turns = [t.strip() for t in raw_corr.split("\n") if t.strip()]

with st.expander(f"💬 Correspondence ({len(turns)} turn{'s' if len(turns) != 1 else ''})",
                 expanded=True):
    if not turns:
        st.caption("No correspondence recorded.")
    else:
        for i, turn in enumerate(turns):
            css_class = "turn turn-odd" if i % 2 == 0 else "turn turn-even"
            label = "Agent" if i % 2 == 0 else "User"
            st.markdown(
                f"<div class='{css_class}'>"
                f"<span style='font-size:12px!important;font-weight:700;"
                f"color:#80868b;text-transform:uppercase;letter-spacing:.06em'>"
                f"Turn {i+1} · {label}</span><br>{turn}"
                f"</div>",
                unsafe_allow_html=True,
            )

st.markdown("<br>", unsafe_allow_html=True)

# ── 5. Root Cause (before diagnostics) ───────────────────────────────────────

if ticket["root_cause_narrative"]:
    st.markdown("#### Root Cause")
    st.markdown(
        f"<div style='background:#e8f0fe;padding:16px 20px;"
        f"border-left:4px solid #1a0dab;border-radius:4px;"
        f"font-size:16px;line-height:1.65'>"
        f"{ticket['root_cause_narrative']}"
        f"</div>",
        unsafe_allow_html=True,
    )
    st.markdown("<br>", unsafe_allow_html=True)

# ── 6. Diagnostics ────────────────────────────────────────────────────────────

st.markdown("#### Diagnostics")

if ticket["diagnostics_summary"]:
    st.markdown(
        f"<div style='color:#3c4043;font-size:16px;margin-bottom:14px;line-height:1.6'>"
        f"{ticket['diagnostics_summary']}</div>",
        unsafe_allow_html=True,
    )

if errors:
    st.markdown("**Observed errors**")
    error_html = " &nbsp;".join(
        f"<code style='background:#fce8e6;color:#c5221f;"
        f"padding:3px 10px;border-radius:4px;font-size:14px'>{e}</code>"
        for e in errors
    )
    st.markdown(error_html, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

if diag_steps:
    st.markdown("**Diagnostic steps**")
    for step in diag_steps:
        num    = step.get("step", "")
        action = step.get("action", "")
        st.markdown(
            f"<div class='step-row'>"
            f"<span class='step-num'>{num}</span>"
            f"<span>{action}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )
else:
    st.caption("No structured diagnostic steps.")

st.markdown("<br>", unsafe_allow_html=True)

# ── 7. Resolution ─────────────────────────────────────────────────────────────

st.markdown("#### Resolution")

if res_steps:
    for i, step in enumerate(res_steps, 1):
        text = step.get("action", str(step)) if isinstance(step, dict) else str(step)
        st.markdown(
            f"<div class='step-row'>"
            f"<span class='step-num'>{i}</span>"
            f"<span>{text}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )
else:
    st.caption("No resolution steps recorded.")
