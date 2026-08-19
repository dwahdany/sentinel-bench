"""Small table/summary helpers shared by the scripts."""

from __future__ import annotations


def render_table(rows, columns):
    """Fixed-width table. ``rows`` are dicts; ``columns`` is the order and the header."""
    widths = {c: max(len(c), *(len(str(r.get(c, ""))) for r in rows)) if rows else len(c)
              for c in columns}
    out = ["  ".join(c.ljust(widths[c]) for c in columns),
           "  ".join("-" * widths[c] for c in columns)]
    for row in rows:
        out.append("  ".join(str(row.get(c, "")).ljust(widths[c]) for c in columns))
    return "\n".join(out)


def pass_rate(records):
    """Fraction of task results with status ok. 0.0 for an empty group."""
    results = [r for r in records if r.get("type") == "task_result"]
    if not results:
        return 0.0
    return sum(1 for r in results if r.get("status") == "ok") / len(results)


def group_by(records, keys):
    """Group records by a tuple of field names, preserving first-seen order."""
    grouped: dict[tuple, list] = {}
    for record in records:
        grouped.setdefault(tuple(record.get(k) for k in keys), []).append(record)
    return grouped
