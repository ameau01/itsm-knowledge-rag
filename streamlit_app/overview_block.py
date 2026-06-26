"""AI Overview render component for the search results page.

Renders the Google-style overview block above the source tickets. 
* When "no proper overview found", show nothing with overview.
* Kept deliberately tight (Google AI Overview style): a one-line lead + a few short key points.
* "Show more" that — within the SAME card — reveals the remaining key points and the diagnostic steps.

"""

from __future__ import annotations

import html
import re

import streamlit as st

# confidence -> (text colour, background, label)
_CHIP = {
    "high":   ("#137333", "#e6f4ea", "High confidence"),
    "medium": ("#b06000", "#fef7e0", "Moderate confidence"),
    "low":    ("#5f6368", "#f1f3f4", "Based on limited evidence"),
}

_CSS = """
<style>
  .ai-ov-head { display:flex; width:100%; align-items:center; justify-content:space-between;
                gap:16px; margin-bottom:6px; }
  .ai-ov-label { font-size:13px; font-weight:600; color:#1a73e8; letter-spacing:.2px;
                 white-space:nowrap; }
  .ai-ov-chip { font-size:12px; font-weight:600; padding:2px 10px; border-radius:10px;
                white-space:nowrap; }
  .ai-ov-lead { font-size:15px; color:#202124; line-height:1.6; margin:0 0 8px 0; }
  .ai-ov-pfx { color:#5f6368; }
  .ai-ov-pts { margin:0; padding-left:18px; }
  .ai-ov-pts li { font-size:14px; color:#3c4043; line-height:1.5; margin-bottom:3px; }
  .ai-ov-alt { font-size:13px; color:#5f6368; margin-top:6px; }
  .ai-ov-prov { font-size:12px; color:#80868b; font-style:italic; margin-top:8px; }
</style>
"""


def _fmt(s: str) -> str:
    """Escape HTML, then render Markdown bold (**x**) so labelled key points show correctly."""
    s = html.escape(s or "")
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)


def _humanize(rc: str) -> str:
    return (rc or "").split("/")[-1].replace("-", " ")


def render_overview(sel) -> None:
    """Render the AI Overview block, or nothing when `sel` is None (no overview found)."""
    if sel is None:
        return
    st.markdown(_CSS, unsafe_allow_html=True)   # inject every render so reruns keep the styles

    ao = sel.ai_overview or {}
    lead = ao.get("lead", "")
    points = [p for p in (ao.get("key_points") or []) if p]
    n = (ao.get("evidence") or {}).get("ticket_count")
    color, bg, label = _CHIP.get(sel.confidence, _CHIP["low"])
    chip = label + (f" · {n} ticket{'s' if (n or 0) != 1 else ''}" if n else "")

    pts_html = "".join(f"<li>{_fmt(p)}</li>" for p in points[:2])
    alt = ""
    if sel.ambiguous and sel.runner_up:
        alt = ("<div class='ai-ov-alt'>Possible alternative: "
               f"<b>{html.escape(_humanize(sel.runner_up))}</b></div>")

    # One bordered card holds the whole overview, including the Show more toggle and its content.
    with st.container(border=True):
        st.markdown(
            "<div class='ai-ov-head'><span class='ai-ov-label'>✦ AI Overview</span>"
            f"<span class='ai-ov-chip' style='color:{color};background:{bg}'>"
            f"{html.escape(chip)}</span></div>"
            "<div class='ai-ov-lead'><span class='ai-ov-pfx'>Your search most closely matches:"
            f"</span> {_fmt(lead)}</div>"
            f"<ul class='ai-ov-pts'>{pts_html}</ul>{alt}",
            unsafe_allow_html=True,
        )

        has_more = len(points) > 2 or (isinstance(sel.diagnostic_steps, list) and sel.diagnostic_steps)
        if not has_more:
            return
        key = f"ov_more_{sel.root_cause_id}"
        expanded = st.session_state.get(key, False)
        if st.button(("Show less ⌃" if expanded else "Show more ⌄"), key=f"btn_{key}"):
            st.session_state[key] = not expanded
            st.rerun()
        if not st.session_state.get(key, False):
            return

        for p in points[2:]:                       # remaining key points
            st.markdown(f"- {p}")

        steps = sel.diagnostic_steps or []          # golden playbook — verbatim, never generated
        if isinstance(steps, list) and steps:
            st.markdown("**Diagnostic steps** — verbatim from the playbook")
            for s in steps:
                if isinstance(s, dict):
                    st.markdown(f"{s.get('step', '')}. {s.get('action', '')}")
                    if s.get("expected_result"):
                        st.caption(f"Expected: {s['expected_result']}")

        if n:
            st.markdown(
                f"<div class='ai-ov-prov'>Synthesized from {n} consolidated "
                f"ticket{'s' if n != 1 else ''}.</div>", unsafe_allow_html=True)
