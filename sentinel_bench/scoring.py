"""Scoring helpers for sentinel-bench runs."""


def exact_match(pred: str, gold: str) -> float:
    """1.0 when pred == gold after strip+lower, else 0.0."""
    return 1.0 if pred.strip().lower() == gold.strip().lower() else 0.0
