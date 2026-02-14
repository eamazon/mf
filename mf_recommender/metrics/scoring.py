"""Composite scoring engine to rank mutual funds."""

import numpy as np


# Weight configuration for the composite score.
# Each weight determines how much that metric matters in the final ranking.
WEIGHTS = {
    "cagr_3y": 0.20,       # 3-year annualized return - medium-term performance
    "cagr_5y": 0.15,       # 5-year annualized return - long-term track record
    "cagr_1y": 0.05,       # 1-year return - recent momentum (low weight to avoid recency bias)
    "sharpe": 0.20,        # Risk-adjusted return - the single best performance metric
    "sortino": 0.10,       # Downside risk-adjusted return
    "consistency": 0.10,   # % of rolling periods with positive returns
    "max_drawdown": 0.10,  # Max peak-to-trough loss (inverted: less negative = better)
    "expense_ratio": 0.05, # Lower expense = better (inverted)
    "alpha": 0.05,         # Manager skill - excess return over benchmark
}


def compute_composite_score(metrics: dict) -> float:
    """Compute a weighted composite score from 0-100.

    Each metric is normalized relative to typical ranges for Indian MFs,
    then weighted and summed.

    Args:
        metrics: dict containing some or all of the keys in WEIGHTS.

    Returns:
        Score from 0 to 100. Higher is better.
    """
    score = 0.0
    total_weight = 0.0

    for metric, weight in WEIGHTS.items():
        raw = metrics.get(metric)
        if raw is None:
            continue
        normalized = _normalize(metric, raw)
        score += normalized * weight
        total_weight += weight

    if total_weight == 0:
        return 0.0
    # Scale to 0-100
    return min(100, max(0, (score / total_weight) * 100))


def _normalize(metric: str, value: float) -> float:
    """Normalize a metric value to roughly 0-1 range.

    Uses typical Indian MF ranges as reference.
    """
    ranges = {
        # (min_bad, max_good) - values outside this range are clipped
        "cagr_1y": (-0.20, 0.40),
        "cagr_3y": (-0.05, 0.30),
        "cagr_5y": (-0.05, 0.25),
        "sharpe": (-0.5, 2.5),
        "sortino": (-0.5, 3.0),
        "consistency": (0.3, 1.0),
        "alpha": (-0.10, 0.10),
    }

    # Inverted metrics: lower is better
    if metric == "max_drawdown":
        # max_drawdown is negative; -0.50 is terrible, -0.05 is great
        return np.clip((-value - 0.05) / 0.45, 0, 1)

    if metric == "expense_ratio":
        # 2.5% is bad, 0.1% is great
        return np.clip((2.5 - value * 100) / 2.4, 0, 1)

    if metric in ranges:
        low, high = ranges[metric]
        return float(np.clip((value - low) / (high - low), 0, 1))

    return 0.5  # Unknown metric, neutral


def score_label(score: float) -> str:
    """Human-readable label for a composite score."""
    if score >= 80:
        return "Excellent"
    if score >= 65:
        return "Very Good"
    if score >= 50:
        return "Good"
    if score >= 35:
        return "Average"
    return "Below Average"
