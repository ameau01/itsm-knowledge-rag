"""
Judge-result disk cache — the main cost saver.

A judge call is the only paid operation in the eval. This memoizes each score by a
content hash of (judge id, metric, query input, retrieval context, expected output), so
re-running the eval — after a crash, a tweak elsewhere, or just iterating — never re-pays
for a case already scored. Identical content across the N variance runs also collapses to
one paid call.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from ..common.contracts import JudgeInput


class JudgeCache:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._data: dict[str, float] = {}
        if self.path.exists():
            try:
                self._data = json.loads(self.path.read_text())
            except (json.JSONDecodeError, OSError):
                self._data = {}

    @staticmethod
    def key(judge_id: str, metric: str, case: JudgeInput) -> str:
        h = hashlib.sha256()
        for part in (judge_id, metric, case.input_text,
                     " ".join(case.retrieval_context), case.expected_output or ""):
            h.update(part.encode("utf-8"))
            h.update(b"\x00")
        return h.hexdigest()

    def get(self, key: str) -> float | None:
        return self._data.get(key)

    def put(self, key: str, value: float) -> None:
        self._data[key] = value
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self._data))
