"""Render the curation eval to a readable table: metric rows x arm columns, mean ± spread."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from .contracts import PageMeta


def format_report(
    agg: Mapping[tuple[str, str], tuple[float, float]],
    *,
    arms: Sequence[str],
    page_meta: Mapping[str, PageMeta],
    judge_name: str,
    n_runs: int,
) -> str:
    metrics = sorted({m for _arm, m in agg})
    singletons = sorted(rc for rc, m in page_meta.items() if not m.multi_ticket)
    multi = sorted(rc for rc, m in page_meta.items() if m.multi_ticket)

    w = max([len(m) for m in metrics] + [22])
    col = 18
    head = "metric".ljust(w) + "".join(a.center(col) for a in arms)
    lines = [
        f"Curation (L2) eval — judge={judge_name}, runs={n_runs}",
        f"pages: {len(page_meta)} ({len(multi)} multi-ticket, {len(singletons)} singleton)",
        "",
        head,
        "-" * len(head),
    ]
    for metric in metrics:
        row = metric.ljust(w)
        for arm in arms:
            cell = agg.get((arm, metric))
            row += ("—".center(col) if cell is None
                    else f"{cell[0]:.3f} ±{cell[1]:.3f}".center(col))
        lines.append(row)

    lines += [
        "",
        f"Variation preservation runs on multi-ticket pages only; {len(singletons)} "
        "singleton(s) excluded from it (kept for faithfulness).",
    ]
    if singletons:
        lines.append("  singletons: " + ", ".join(singletons))
    return "\n".join(lines)
