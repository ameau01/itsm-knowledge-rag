"""
Report assembly — the headline tables from docs/retrieval-evaluation.md.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from ..common.bootstrap import CI
from ..common.relevance import LENIENT, STRICT
from .abstention import AbstentionReport

TABLE1_K = 10


@dataclass(frozen=True)
class Column:
    metric: str  # "recall"
    level: str   # STRICT | LENIENT
    label: str   # column header, e.g. "Recall@10 (strict)"


# The golden Table 1 columns (docs/retrieval-evaluation.md). Hit Rate is not here.
TABLE1_COLUMNS: tuple[Column, ...] = (
    Column("recall", STRICT, "Recall@10 (strict)"),
    Column("recall", LENIENT, "Recall@10 (family)"),
)


@dataclass(frozen=True)
class TableCell:
    point: float
    lo: float
    hi: float


@dataclass(frozen=True)
class ArmRow:
    arm: str
    cells: dict[str, TableCell]  # keyed by column label


@dataclass(frozen=True)
class Table:
    title: str
    columns: tuple[str, ...]  # column labels, in order
    rows: list[ArmRow]        # ordered best-first by the first column


def build_arm_table(
    agg: dict[tuple, CI],
    arms: Sequence[str],
    columns: Sequence[Column] = TABLE1_COLUMNS,
    k: int = TABLE1_K,
    title: str = "Table 1: retrieval performance (@10)",
) -> Table:
    """Assemble one arm-comparison table from an aggregate dict keyed
    (arm, metric, k, level)."""
    rows: list[ArmRow] = []
    for arm in arms:
        cells: dict[str, TableCell] = {}
        for col in columns:
            ci = agg.get((arm, col.metric, k, col.level))
            if ci is not None:
                cells[col.label] = TableCell(ci.point, ci.lo, ci.hi)
        rows.append(ArmRow(arm=arm, cells=cells))
    # order best-first by the first (primary) column's point estimate
    primary = columns[0].label
    rows.sort(key=lambda r: r.cells.get(primary, TableCell(0, 0, 0)).point, reverse=True)
    return Table(title=title, columns=tuple(c.label for c in columns), rows=rows)


def to_markdown(table: Table) -> str:
    header = "| Arm | " + " | ".join(table.columns) + " |"
    sep = "|" + "---|" * (len(table.columns) + 1)
    lines = [f"**{table.title}**", "", header, sep]
    for row in table.rows:
        cells = []
        for label in table.columns:
            c = row.cells.get(label)
            cells.append(f"{c.point:.3f} [{c.lo:.3f}, {c.hi:.3f}]" if c else "—")
        lines.append(f"| {row.arm} | " + " | ".join(cells) + " |")
    return "\n".join(lines)


# ── complex + abstention renderers (the eval-set's other two axes) ────────────────
def complex_to_markdown(
    recall_by_arm: dict[str, float],
    arms: Sequence[str],
    k: int = TABLE1_K,
    title: str = "Complex queries: candidate-set recall",
) -> str:
    """Per-arm mean candidate-set recall@k over the complex (multi-label) queries, best
    arm first."""
    lines = [f"**{title} (@{k})**", "", f"| Arm | Candidate-set recall@{k} |", "|---|---|"]
    for arm in sorted(arms, key=lambda a: recall_by_arm.get(a, 0.0), reverse=True):
        v = recall_by_arm.get(arm)
        lines.append(f"| {arm} | " + (f"{v:.3f}" if v is not None else "—") + " |")
    return "\n".join(lines)


def abstention_to_markdown(
    reports_by_arm: dict[str, AbstentionReport],
    arms: Sequence[str],
    title: str = "Abstention",
) -> str:
    """Per-arm abstention accuracy and false-abstention rate against the calibrated floor."""
    lines = [f"**{title}**", "",
             "| Arm | Abstention accuracy | False-abstention rate |", "|---|---|---|"]
    for arm in arms:
        rep = reports_by_arm.get(arm)
        if rep is None:
            lines.append(f"| {arm} | — | — |")
        else:
            lines.append(
                f"| {arm} | {rep.abstention_accuracy:.3f} | {rep.false_abstention_rate:.3f} |")
    return "\n".join(lines)
