"""Plain-English explanations of financial metrics for non-professionals."""


METRIC_EXPLANATIONS = {
    "cagr_1y": {
        "name": "1-Year Return",
        "short": "How much the fund grew in the last 1 year",
        "detail": (
            "If you had invested Rs 1,00,000 one year ago, this tells you how much "
            "it would be worth today. A 15% return means it became Rs 1,15,000."
        ),
        "good": "Higher is better. Compare within the same category.",
        "format": "percent",
    },
    "cagr_3y": {
        "name": "3-Year Return (CAGR)",
        "short": "Average annual growth over the last 3 years",
        "detail": (
            "CAGR = Compound Annual Growth Rate. This smooths out yearly ups and downs "
            "to show the average growth per year. 3 years is the most common period "
            "to judge a fund's medium-term track record."
        ),
        "good": "Higher is better. 12-18% is good for equity funds in India.",
        "format": "percent",
    },
    "cagr_5y": {
        "name": "5-Year Return (CAGR)",
        "short": "Average annual growth over the last 5 years",
        "detail": (
            "Same as 3-year CAGR but over a longer period. More reliable because "
            "it likely includes both bull and bear markets, giving a truer picture."
        ),
        "good": "Higher is better. 10-15% is good for equity funds in India.",
        "format": "percent",
    },
    "consistency": {
        "name": "Consistency Score",
        "short": "How often the fund delivers positive returns",
        "detail": (
            "Looks at every rolling 1-year window over the last 5 years and counts "
            "what percentage of those windows had positive returns. A fund with 90% "
            "consistency made money in 9 out of 10 rolling years."
        ),
        "good": "Higher is better. Above 80% is very consistent.",
        "format": "percent",
    },
    "volatility": {
        "name": "Volatility (Std Dev)",
        "short": "How much the fund's value bounces around day-to-day",
        "detail": (
            "Standard deviation measures how wildly the fund's daily returns swing. "
            "Think of it as the 'bumpiness' of the ride. A fund with 20% volatility "
            "will have bigger day-to-day swings than one with 10%."
        ),
        "good": "Lower is better (smoother ride). 10-15% is typical for large cap equity.",
        "format": "percent",
    },
    "sharpe": {
        "name": "Sharpe Ratio",
        "short": "Return earned per unit of risk taken",
        "detail": (
            "Imagine two funds both returned 15%, but Fund A was a smooth ride while "
            "Fund B was a roller-coaster. Sharpe Ratio rewards Fund A because it "
            "achieved the same return with less risk. It asks: 'Was the risk worth it?'"
        ),
        "good": "Higher is better. Below 1 = poor, 1-2 = good, above 2 = excellent.",
        "format": "decimal",
    },
    "sortino": {
        "name": "Sortino Ratio",
        "short": "Like Sharpe, but only penalizes bad (downside) volatility",
        "detail": (
            "Sharpe treats all volatility as bad, but going UP a lot isn't actually bad! "
            "Sortino only counts the downward swings as risk. This is more fair because "
            "it doesn't penalize a fund for having big positive days."
        ),
        "good": "Higher is better. Same scale as Sharpe but usually slightly higher.",
        "format": "decimal",
    },
    "max_drawdown": {
        "name": "Max Drawdown",
        "short": "The worst peak-to-valley loss the fund ever experienced",
        "detail": (
            "If the fund was at Rs 100 and dropped to Rs 65 before recovering, "
            "the max drawdown is -35%. This shows you the worst-case scenario - "
            "the maximum pain you could have experienced if you invested at the peak."
        ),
        "good": "Closer to 0% is better. -20% to -40% is typical for equity funds.",
        "format": "percent",
    },
    "beta": {
        "name": "Beta",
        "short": "How much the fund moves with the overall market (Nifty 50)",
        "detail": (
            "Beta = 1.0 means the fund moves exactly with the market. "
            "Beta = 1.3 means when the market goes up 10%, this fund tends to go up 13% "
            "(and down 13% when market falls 10%). "
            "Beta = 0.7 means it only moves 70% as much as the market."
        ),
        "good": "Depends on your preference: <1 for stability, >1 for aggression.",
        "format": "decimal",
    },
    "alpha": {
        "name": "Alpha",
        "short": "Extra return the fund manager generated above what the market gave",
        "detail": (
            "After accounting for the market's performance and the fund's risk level, "
            "alpha tells you if the fund manager actually added value. "
            "Positive alpha = the manager beat expectations. Negative = underperformed."
        ),
        "good": "Positive is good. Even 1-2% alpha is significant over time.",
        "format": "percent",
    },
    "expense_ratio": {
        "name": "Expense Ratio",
        "short": "Annual fee charged by the fund house (deducted from your returns)",
        "detail": (
            "Every fund charges an annual management fee. If a fund returned 15% but "
            "has a 1.5% expense ratio, your net return is ~13.5%. Over 20 years, "
            "even a 0.5% difference in fees can mean lakhs less in your corpus. "
            "Direct plans always have lower expense ratios than Regular plans."
        ),
        "good": "Lower is better. Below 0.5% is great, above 2% is expensive.",
        "format": "percent_raw",
    },
    "aum": {
        "name": "AUM (Assets Under Management)",
        "short": "Total money managed by this fund (in crores)",
        "detail": (
            "Larger AUM generally means more investor confidence and better liquidity. "
            "But very large AUM can hurt small-cap/mid-cap funds because buying big "
            "positions in small companies becomes harder."
        ),
        "good": "Sweet spot: Rs 500-50,000 Cr for equity funds.",
        "format": "currency_cr",
    },
    "composite_score": {
        "name": "Overall Score",
        "short": "Combined score weighing returns, risk, and consistency (0-100)",
        "detail": (
            "We combine multiple metrics into a single score: "
            "35% weight on returns (1y, 3y, 5y), "
            "30% weight on risk-adjusted returns (Sharpe, Sortino), "
            "20% weight on safety (consistency, max drawdown), "
            "10% weight on alpha, and 5% on low expense ratio. "
            "This gives a balanced view across performance, risk, and cost."
        ),
        "good": "80+ Excellent, 65-80 Very Good, 50-65 Good, 35-50 Average.",
        "format": "score",
    },
}


def explain(metric: str, verbose: bool = False) -> str:
    """Get a plain-English explanation of a metric."""
    info = METRIC_EXPLANATIONS.get(metric)
    if not info:
        return f"Unknown metric: {metric}"
    parts = [f"{info['name']}: {info['short']}"]
    if verbose:
        parts.append(info["detail"])
        parts.append(f"What's good: {info['good']}")
    return "\n".join(parts)


def format_value(metric: str, value: float) -> str:
    """Format a metric value for display."""
    info = METRIC_EXPLANATIONS.get(metric, {})
    fmt = info.get("format", "decimal")
    if value is None:
        return "N/A"
    if fmt == "percent":
        return f"{value * 100:+.1f}%" if "drawdown" in metric or "alpha" in metric else f"{value * 100:.1f}%"
    if fmt == "percent_raw":
        return f"{value:.2f}%"
    if fmt == "decimal":
        return f"{value:.2f}"
    if fmt == "currency_cr":
        return f"Rs {value:,.0f} Cr"
    if fmt == "score":
        return f"{value:.0f}/100"
    return f"{value:.2f}"
