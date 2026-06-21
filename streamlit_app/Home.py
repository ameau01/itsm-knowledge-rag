"""
ITSM Knowledge Search — landing page (Home).

A blank, Google-style search box. Type a problem in natural language and submit to run live
hybrid retrieval; results render on the Search results page. A short, hand-curated list of
example queries sits beneath the box (text only). "I'm Feeling Lucky" runs a random query from
the frozen eval-set.
"""

import json
import pathlib
import random

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# Example queries shown under the search box. Edit this list freely.
HINTS = [
    "504 timeout error",
    "SSL expired warnings",
    "Outlook desktop disconnected",
]

st.set_page_config(
    page_title="ITSM Knowledge Search",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
      /* Display face for the logo. Poppins = clean geometric, close to Product Sans.
         Swap the family below to Fredoka for a softer, more "logo" feel. */
      @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@600;700&family=Fredoka:wght@500;600&display=swap');

      #MainMenu { visibility: hidden; } footer { visibility: hidden; }
      section[data-testid="stSidebar"] { display: none; }
      .block-container { padding-top: 8rem !important; max-width: 680px; }

      /* ── search box: white fill, hairline border, shadow on focus ── */
      div[data-testid="stTextInput"] input {
          font-size: 16px;
          padding: 0.85rem 1.35rem;
          border-radius: 26px;
          border: 1px solid #dfe1e5;
          background: #ffffff;
          color: #202124;
          box-shadow: none;
          transition: box-shadow .18s ease, border-color .18s ease;
      }
      div[data-testid="stTextInput"] input:hover {
          border-color: #dfe1e5;
          box-shadow: 0 1px 6px rgba(32,33,36,.18);
      }
      div[data-testid="stTextInput"] input:focus {
          border-color: transparent;
          box-shadow: 0 1px 6px rgba(32,33,36,.28);
          outline: none;
      }
      div[data-testid="stTextInput"] input::placeholder {
          color: #9aa0a6;
      }

      /* ── buttons: small, light-gray Google style with hairline border ── */
      div[data-testid="stFormSubmitButton"] button {
          border-radius: 4px;
          font-weight: 400;
          font-size: 13px;
          padding: 0.45rem 1.1rem;
          background: #f8f9fa;
          color: #3c4043;
          border: 1px solid #f8f9fa;
          box-shadow: none;
          transition: border-color .15s ease, box-shadow .15s ease, background .15s ease;
      }
      div[data-testid="stFormSubmitButton"] button:hover {
          border: 1px solid #dadce0;
          box-shadow: 0 1px 1px rgba(0,0,0,.08);
          background: #f8f9fa;
          color: #202124;
      }
      div[data-testid="stFormSubmitButton"] button:focus:not(:active) {
          border: 1px solid #4285f4;
          color: #202124;
      }

      /* keep the action buttons centered as a tight pair, Google-style */
      div[data-testid="stForm"] [data-testid="column"] {
          display: flex;
          justify-content: center;
      }
      div[data-testid="stFormSubmitButton"] button { min-width: 130px; }

      /* ── multi-color wordmark ── */
      .wordmark {
          text-align: center;
          white-space: nowrap;          /* never break "Search" across lines */
          font-family: 'Fredoka', sans-serif;
          font-size: 42px;
          font-weight: 600;
          letter-spacing: 0px;
          margin-bottom: 6px;
          line-height: 1.1;
      }
      /* If the wordmark ever clips on a narrow viewport, the box-container
         clamp below keeps it scaling down instead of overflowing. */
      @media (max-width: 560px) {
          .wordmark { font-size: 34px; }
      }
      /* OPTIONAL bounded box around the wordmark — uncomment to enable.
         Google's real logo has no box; this is your own twist if you want it.
      .wordmark {
          display: inline-block;
          width: auto;
          padding: 14px 28px;
          border: 1px solid #dfe1e5;
          border-radius: 12px;
          box-shadow: 0 1px 6px rgba(32,33,36,.12);
      }
      .wordmark-wrap { text-align: center; }
      */
      .wordmark .c1 { color: #4285f4; }  /* blue   */
      .wordmark .c2 { color: #ea4335; }  /* red    */
      .wordmark .c3 { color: #fbbc05; }  /* yellow */
      .wordmark .c4 { color: #4285f4; }  /* blue   */
      .wordmark .c5 { color: #34a853; }  /* green  */
      .wordmark .c6 { color: #ea4335; }  /* red    */

      .subtitle {
          text-align: center;
          color: #5f6368;
          font-size: 14px;
          margin: 0 0 34px 0;
      }

      /* example-query hints (static text, not clickable) */
      .hints-label { text-align:center; color:#9aa0a6; font-size:11px; letter-spacing:.6px;
                     text-transform:uppercase; margin: 34px 0 8px 0; }
      .hints { text-align:center; color:#80868b; font-size:12.5px; line-height:1.95; }

      /* repo link — small and quiet, but clearly clickable on hover */
      .repo-footer { text-align:center; margin-top: 110px; line-height: 1.8; }
      .repo-footer a {
          color: #80868b; font-size: 12.5px; text-decoration: none;
          display: inline-flex; align-items: center; gap: 6px;
          transition: color .15s ease;
      }
      .repo-footer a:hover { color: #1a73e8; text-decoration: underline; }
      .repo-footer svg { width: 15px; height: 15px; fill: currentColor; }
      .repo-byline { color: #9aa0a6; font-size: 11.5px; margin-top: 4px; }

      /* ── button row: center the two submit buttons as a paired, wrapping group ──
         The form stacks its children vertically by default. We grab the block that
         holds the two submit buttons and make it a centered flex row instead. */
      div[data-testid="stForm"] [data-testid="stVerticalBlock"]:has(> div [data-testid="stFormSubmitButton"]) {
          flex-direction: row;
          flex-wrap: wrap;
          justify-content: center;
          gap: 10px;
      }
      /* Fallback for browsers/DOM where :has() doesn't catch: still center each
         button and cap its width so it never goes full-bleed on mobile. */
      div[data-testid="stForm"] [data-testid="element-container"]:has([data-testid="stFormSubmitButton"]) {
          display: flex;
          justify-content: center;
      }
      div[data-testid="stFormSubmitButton"] {
          width: auto !important;
          flex: 0 0 auto;
      }
      div[data-testid="stFormSubmitButton"] button {
          width: auto;
          min-width: 140px;
          max-width: 240px;
          margin-top: 8px;
      }
      @media (max-width: 480px) {
          .repo-footer { margin-top: 80px; }
      }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def eval_queries() -> list[str]:
    """All simple eval-set queries, used by the I'm-Feeling-Lucky pick."""
    path = (pathlib.Path(__file__).resolve().parents[1]
            / "eval-set" / "retrieval" / "simple-queries.json")
    try:
        return [q["query"] for q in json.loads(path.read_text())["queries"]]
    except Exception:
        return []


def _go(text: str) -> None:
    st.session_state["sec_q"] = text.strip()
    st.switch_page("pages/Search_results.py")


# ── header: multi-color wordmark ──────────────────────────────────────────────────
# If you enable the optional .wordmark box in the CSS above, this wrapper centers it.
st.markdown(
    "<div class='wordmark-wrap'><div class='wordmark'>"
    "<span class='c1'>I</span><span class='c2'>T</span><span class='c3'>S</span><span class='c4'>M</span>"
    "<span class='gap'>&nbsp;</span>"
    "<span class='c5'>Knowledge</span>"
    "<span class='gap'>&nbsp;</span>"
    "<span class='c6'>Search</span>"
    "</div></div>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p class='subtitle'>Describe a problem in plain language. "
    "Hybrid retrieval finds the closest prior tickets.</p>",
    unsafe_allow_html=True,
)

# ── search box + actions ──────────────────────────────────────────────────────────
with st.form("search_form", clear_on_submit=False, border=False):
    typed = st.text_input(
        "search",
        placeholder="e.g. nightly sync jobs failing with 504 timeouts after token expiry",
        label_visibility="collapsed",
    )
    # Both buttons in normal flow; the CSS below turns the form's button row
    # into a centered flex container that keeps them paired on every screen.
    search_clicked = st.form_submit_button("Search")
    lucky_clicked = st.form_submit_button("I'm Feeling Lucky")

if search_clicked and typed.strip():
    _go(typed)
elif lucky_clicked:
    pool = eval_queries()
    if pool:
        _go(random.choice(pool))

# ── example-query hints (static list, smaller font) ───────────────────────────────
if HINTS:
    st.markdown("<div class='hints-label'>example queries</div>", unsafe_allow_html=True)
    st.markdown("<div class='hints'>" + "<br>".join(HINTS) + "</div>", unsafe_allow_html=True)

# ── repo link (small, Google-footer style) ────────────────────────────────────────
st.markdown(
    "<div class='repo-footer'>"
    "<a href='https://github.com/ameau01/itsm-knowledge-rag' target='_blank' rel='noopener'>"
    "<svg viewBox='0 0 16 16' aria-hidden='true'>"
    "<path d='M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 "
    "0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 "
    "1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 "
    "0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 "
    "2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 "
    "1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 "
    "2.2 0 .21.15.46.55.38A8.01 8.01 0 0016 8c0-4.42-3.58-8-8-8z'/></svg>"
    "View source on GitHub</a>"
    "<div class='repo-byline'>Built by Alexander Meau</div>"
    "</div>",
    unsafe_allow_html=True,
)
