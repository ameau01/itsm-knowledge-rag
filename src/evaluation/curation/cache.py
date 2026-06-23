"""Curation judge cache — separate file from the L1 cache, by design.

Default path lives under eval/results/ (already gitignored); nothing here touches the L1
cache file.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .contracts import CurationCase

_PROJECT = Path(__file__).resolve().parents[3]
DEFAULT_CACHE = _PROJECT / "eval" / "results" / "curation_judge_cache.json"


class CurationCache:
    def __init__(self, path: str | Path = DEFAULT_CACHE) -> None:
        self.path = Path(path)
        self._data: dict[str, float] = {}
        if self.path.exists():
            try:
                self._data = json.loads(self.path.read_text())
            except (json.JSONDecodeError, OSError):
                self._data = {}

    @staticmethod
    def key(judge_id: str, case: CurationCase) -> str:
        h = hashlib.sha256()
        for part in (
            judge_id,
            case.metric,
            case.input_text,
            " ".join(case.retrieval_context),
            case.actual_output,          # generation-aware: the L1 cache omits this
            case.expected_output or "",
        ):
            h.update(part.encode("utf-8"))
            h.update(b"\x00")
        return h.hexdigest()

    def get(self, key: str) -> float | None:
        return self._data.get(key)

    def put(self, key: str, value: float) -> None:
        self._data[key] = value
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self._data))
