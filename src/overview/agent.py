"""The overview agent — include system prompt, and Pydantic output schema.
"""

from __future__ import annotations

import re

# --------------------------------------------------------------------------- #
# Per-tier hedge — injected into the prompt so the lead is written at the right confidence.
# --------------------------------------------------------------------------- #
HEDGE = {
    "high":   "This page is well supported (>=10 tickets, confirmed). State the cause directly but "
              "still as the issue's cause, e.g. 'The cause is ...'. Do not overclaim certainty.",
    "medium": "This page has moderate support (3-9 tickets). Hedge the lead: 'The likely cause is "
              "...'. Avoid flat assertion.",
    "low":    "This page rests on very little evidence (<=2 tickets) or its root cause is marked "
              "unconfirmed/indeterminate. Treat the cause as an UNVERIFIED HYPOTHESIS, not a "
              "finding. Use possibility wording and tentative verbs only — 'may be', 'might be', "
              "'could be', 'appears consistent with', 'one possible cause is'. Open with the "
              "uncertainty, e.g. 'Based on limited evidence, a possible cause may be ...'. Do NOT "
              "use 'confirm', 'confirmed', 'probable', 'the cause is', 'caused by', or any phrasing "
              "that presents the cause as established; make clear it still needs verification.",
}


SYSTEM_PROMPT = """\
You write a short, Google-style AI OVERVIEW for an internal IT knowledge-base issue. The overview is
the page-level "answer": it names the most likely root cause of a known issue in plain language, so
a reader can recognise whether this is their problem before reading the full page. How firmly the
cause is stated depends on the CONFIDENCE guidance given in the user message.

You are given a CURATED DESCRIPTION (title, symptoms, cause, variations, a plain-language
diagnostic_summary, reporting). Write only from it. Output two things:

- lead: ONE sentence that fuses the symptom and the likely cause into the whole answer. Put the
  most important information first; the reader may only see this sentence before expanding. Aim for
  <= ~200 characters for the core statement (a confidence hedge prefix may add a little).
- key_points: 3 short points (fewer if the source lacks the material — never pad). In order:
    1. Common pattern  — how the issue presents, from `symptoms` (recognition: "is this me?").
    2. Scope / variation — breadth or notable exceptions, from `variations`.
    3. How it's identified — a plain-language summary of the diagnostic signal, from
       `diagnostic_summary`. This is the BRIDGE to the verbatim diagnostic steps shown below the
       overview; summarise how the issue is recognised, do NOT write or number any procedure step.
  Each point starts with a short bold label, e.g. "**Common pattern:** ...".

HARD RULES
- Third person about "affected users" / "the issue". Never second person, never "you", never a
  question. Documentation voice, plain language.
- Probabilistic per the confidence guidance given below. Do not overclaim.
- Faithful: state only what the curated description supports. Invent no error codes, hostnames,
  policy names, OS versions, or counts. Keep redaction placeholders (<PERSON>, <USER>, <HOSTNAME>,
  <LOCATION>, <EMAIL>) verbatim if they appear.
- Do NOT reference a search or query (there is none here). Do NOT restate the title or the reporting
  line. Do NOT include diagnostic or resolution STEPS.
"""

USER_TEMPLATE = """\
CONFIDENCE: {tier}
{hedge}

CURATED DESCRIPTION (the only source):
  title: {title}

  symptoms:
{symptoms}

  cause:
{cause}

  variations:
{variations}

  diagnostic_summary:
{diagnostic_summary}

Write the lead and key_points now.
"""


def build_prompt(cd: dict, tier: str) -> tuple[str, str]:
    """Assemble (system, user) for one page. Deterministic — byte-identical given (cd, tier).

    NOTE: the 5-field curation has no `diagnostic_summary`, so that block renders "(none)" and the
    model naturally drops the "how it's identified" point — the intended behaviour.
    """
    def block(text):
        text = (text or "").strip()
        return "\n".join("    " + ln for ln in text.splitlines()) if text else "    (none)"
    user = USER_TEMPLATE.format(
        tier=tier.upper(), hedge=HEDGE[tier],
        title=(cd.get("title") or "").strip() or "(none)",
        symptoms=block(cd.get("symptoms")), cause=block(cd.get("cause")),
        variations=block(cd.get("variations")), diagnostic_summary=block(cd.get("diagnostic_summary")),
    )
    return SYSTEM_PROMPT, user


# --------------------------------------------------------------------------- #
# Text helpers (used by the mock generator)
# --------------------------------------------------------------------------- #
def _first_sentence(s: str | None) -> str:
    s = (s or "").strip().replace("\n", " ")
    if not s:
        return ""
    return re.split(r"(?<=[.!?])\s", s)[0].strip()


def _first_line(s: str | None) -> str:
    for line in (s or "").splitlines():
        line = line.strip().lstrip("-•*").strip()
        if line:
            return line
    return ""


def mock_generate(cd: dict, tier: str) -> dict:
    """Deterministic placeholder (no API): tier-aware lead + points from the curated fields."""
    prefix = {"high": "", "medium": "Likely cause: ",
              "low": "Based on limited evidence, a possible cause may be: "}[tier]
    lead = (prefix + _first_sentence(cd.get("cause"))).strip() or "MOCK overview."
    kp = []
    if (s := _first_sentence(cd.get("symptoms"))):
        kp.append(f"**Common pattern:** {s}")
    if (v := _first_line(cd.get("variations"))):
        kp.append(f"**Scope:** {v}")
    if (d := _first_sentence(cd.get("diagnostic_summary"))):
        kp.append(f"**How it's identified:** {d}")
    return {"lead": lead, "key_points": kp[:3]}


# --------------------------------------------------------------------------- #
# The agent — holds the structured LLM, built once per run.
# --------------------------------------------------------------------------- #
class OverviewAgent:
    """LLM-only generator. Provider switch (anthropic/openai). Built once; `generate` per page."""

    def __init__(self, provider: str = "anthropic", model: str | None = None,
                 temperature: float = 0.0) -> None:
        try:
            from langchain_core.messages import HumanMessage, SystemMessage
            from pydantic import BaseModel, Field
        except ImportError:
            raise SystemExit("Missing deps. Run: uv sync --group overview")

        class Overview(BaseModel):
            lead: str = Field(description="one sentence fusing symptom + probable cause; answer-first, ~<=200 chars")
            key_points: list[str] = Field(description="3 bold-labelled points: common pattern, scope/variation, how it's identified; fewer if unsupported")

        provider = (provider or "anthropic").lower()
        model = model or ("gpt-4o" if provider == "openai" else "claude-opus-4-8")
        if provider == "openai":
            try:
                from langchain_openai import ChatOpenAI
            except ImportError:
                raise SystemExit("Provider 'openai' needs langchain-openai. Run: uv add langchain-openai")
            llm = ChatOpenAI(model=model, temperature=temperature)
        else:
            try:
                from langchain_anthropic import ChatAnthropic
            except ImportError:
                raise SystemExit("Provider 'anthropic' needs langchain-anthropic. Run: uv sync --group overview")
            llm = ChatAnthropic(model=model, temperature=temperature, max_tokens=1200)

        self.provider, self.model = provider, model
        self.label = f"{provider}:{model}"
        self._structured = llm.with_structured_output(Overview)
        self._SystemMessage, self._HumanMessage = SystemMessage, HumanMessage

    def generate(self, cd: dict, tier: str) -> dict:
        system, user = build_prompt(cd, tier)
        resp = self._structured.invoke(
            [self._SystemMessage(content=system), self._HumanMessage(content=user)])
        data = resp.model_dump() if hasattr(resp, "model_dump") else dict(resp)
        return {"lead": (data.get("lead") or "").strip(),
                "key_points": [k.strip() for k in (data.get("key_points") or []) if k and k.strip()]}
