"""
Section contract tests — corpus/sections.py.

render_section is the shared flatten the indexer and the eval reader both use, so the
embedded text and the resolved text match. Pure (no DB), runs everywhere.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))  # src/ on path

from corpus.sections import SECTION_COLUMNS, SECTION_NAMES, render_section


def test_render_passes_plain_text_and_handles_none():
    assert render_section("plain text") == "plain text"
    assert render_section(None) == ""
    assert render_section("") == ""


def test_render_flattens_json_string_array():
    # resolution_steps shape: ["step one", "step two"] -> clean newline join.
    assert render_section('["a", "b"]') == "a\nb"


def test_render_bare_json_object_flattens_to_key_values():
    # The dict branch fires only for a BARE json object.
    assert render_section('{"step": 1, "action": "x"}') == "step: 1; action: x"


def test_render_list_of_objects_keeps_python_repr():
    # KNOWN, PRESERVED behavior: diagnostics_procedure is a JSON ARRAY of objects. Each
    # parsed dict reaches render_section as a python object whose str() is not valid JSON,
    # so it renders as its python repr (single quotes), NOT "k: v". Flagged in
    # eval-graduation-refactor.md for a pre-indexer decision; pinned here so any change is
    # deliberate.
    out = render_section('[{"step": 1, "action": "x"}]')
    assert out == "{'step': 1, 'action': 'x'}"


def test_render_non_json_bracketed_text_passes_through():
    # malformed JSON starting with '[' must not raise — returns the raw string.
    assert render_section("[not json") == "[not json"


def test_section_names_order_is_stable():
    assert SECTION_NAMES == ("description", "correspondence", "diagnostics", "resolution")
    assert tuple(SECTION_COLUMNS) == SECTION_NAMES


def test_section_columns_map_to_store_columns():
    assert SECTION_COLUMNS["description"] == "submitted_description"
    assert SECTION_COLUMNS["diagnostics"] == "diagnostics_procedure"
    assert SECTION_COLUMNS["resolution"] == "resolution_steps"
