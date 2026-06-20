"""
Table 2 (semantic quality) assembly. Judge scores carry mean ± stdev across the N runs
(vs Table 1's bootstrap CIs). Same four arms, a different angle.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from .base import CONTEXTUAL_PRECISION, CONTEXTUAL_RELEVANCY

TABLE2_METRICS: tuple[tuple[str, str], ...] = (
    (CONTEXTUAL_PRECISION, "Contextual Precision"),
    (CONTEXTUAL_RELEVANCY, "Contextual Relevancy"),
)


@dataclass(frozen=True)
class JudgeCell:
    mean: float
    stdev: float


@dataclass(frozen=True)
class JudgeRow:
    arm: str
    cells: dict[str, JudgeCell]


@dataclass(frozen=True)
class JudgeTable:
    title: str
    columns: tuple[str, ...]
    rows: list[JudgeRow]


def build_table2(
    agg: dict[tuple[str, str], tuple[float, float]],
    arms: Sequence[str],
    title: str = "Table 2: semantic quality (DeepEval judge)",
) -> JudgeTable:
    rows: list[JudgeRow] = []
    for arm in arms:
        cells: dict[str, JudgeCell] = {}
        for metric, label in TABLE2_METRICS:
            v = agg.get((arm, metric))
            if v is not None:
                cells[label] = JudgeCell(v[0], v[1])
        rows.append(JudgeRow(arm, cells))
    primary = TABLE2_METRICS[0][1]
    rows.sort(key=lambda r: r.cells.get(primary, JudgeCell(0.0, 0.0)).mean, reverse=True)
    return JudgeTable(title, tuple(label for _, label in TABLE2_METRICS), rows)


def to_markdown(table: JudgeTable) -> str:
    header = "| Arm | " + " | ".join(table.columns) + " |"
    sep = "|" + "---|" * (len(table.columns) + 1)
    lines = [f"**{table.title}**", "", header, sep]
    for row in table.rows:
        cells = []
        for label in table.columns:
            c = row.cells.get(label)
            cells.append(f"{c.mean:.3f} ± {c.stdev:.3f}" if c else "—")
        lines.append(f"| {row.arm} | " + " | ".join(cells) + " |")
    return "\n".join(lines)
