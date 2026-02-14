"""Risk metric calculations from NAV time series."""

import pandas as pd
import numpy as np
from .returns import daily_returns

# Approximate risk-free rate for India (use 91-day T-bill rate ~6.5% annualized)
RISK_FREE_RATE_ANNUAL = 0.065
RISK_FREE_RATE_DAILY = (1 + RISK_FREE_RATE_ANNUAL) ** (1 / 252) - 1
TRADING_DAYS_PER_YEAR = 252


def volatility(nav_series: pd.Series, years: int = 3) -> float | None:
    """Annualized standard deviation of daily returns (last N years).

    Higher = more volatile = riskier. Typically 10-25% for equity funds.
    """
    dr = _trim_daily_returns(nav_series, years)
    if dr is None or len(dr) < 60:
        return None
    return float(dr.std() * np.sqrt(TRADING_DAYS_PER_YEAR))


def sharpe_ratio(nav_series: pd.Series, years: int = 3) -> float | None:
    """Sharpe Ratio: (annualized return - risk-free rate) / volatility.

    Measures risk-adjusted return. Higher is better.
    - < 1.0: Sub-par
    - 1.0 - 2.0: Good
    - > 2.0: Excellent
    """
    dr = _trim_daily_returns(nav_series, years)
    if dr is None or len(dr) < 60:
        return None
    excess = dr - RISK_FREE_RATE_DAILY
    if dr.std() == 0:
        return None
    return float(excess.mean() / dr.std() * np.sqrt(TRADING_DAYS_PER_YEAR))


def sortino_ratio(nav_series: pd.Series, years: int = 3) -> float | None:
    """Sortino Ratio: like Sharpe but uses only downside deviation.

    Better than Sharpe because upside volatility isn't bad.
    Higher is better; same scale as Sharpe.
    """
    dr = _trim_daily_returns(nav_series, years)
    if dr is None or len(dr) < 60:
        return None
    excess = dr - RISK_FREE_RATE_DAILY
    downside = excess[excess < 0]
    if len(downside) < 10:
        return None
    downside_std = np.sqrt((downside ** 2).mean())
    if downside_std == 0:
        return None
    return float(excess.mean() / downside_std * np.sqrt(TRADING_DAYS_PER_YEAR))


def max_drawdown(nav_series: pd.Series) -> float | None:
    """Maximum drawdown: largest peak-to-trough decline.

    Returns a negative number (e.g., -0.35 = 35% max loss).
    Closer to 0 is better.
    """
    if nav_series.empty or len(nav_series) < 2:
        return None
    cummax = nav_series.cummax()
    drawdowns = (nav_series - cummax) / cummax
    return float(drawdowns.min())


def beta(nav_series: pd.Series, benchmark_series: pd.Series, years: int = 3) -> float | None:
    """Beta: sensitivity of fund returns to benchmark (market) returns.

    - beta = 1.0: moves exactly with market
    - beta > 1.0: more volatile than market (amplifies moves)
    - beta < 1.0: less volatile than market (dampens moves)
    """
    fund_dr = _trim_daily_returns(nav_series, years)
    bench_dr = _trim_daily_returns(benchmark_series, years)
    if fund_dr is None or bench_dr is None:
        return None
    # Align on common dates
    common = fund_dr.index.intersection(bench_dr.index)
    if len(common) < 60:
        return None
    f = fund_dr.loc[common]
    b = bench_dr.loc[common]
    cov = np.cov(f, b)
    if cov[1, 1] == 0:
        return None
    return float(cov[0, 1] / cov[1, 1])


def alpha(nav_series: pd.Series, benchmark_series: pd.Series, years: int = 3) -> float | None:
    """Jensen's Alpha: excess return above what beta would predict.

    Positive alpha = fund beat its expected return given its risk.
    Measures manager skill.
    """
    b = beta(nav_series, benchmark_series, years)
    if b is None:
        return None
    fund_dr = _trim_daily_returns(nav_series, years)
    bench_dr = _trim_daily_returns(benchmark_series, years)
    if fund_dr is None or bench_dr is None:
        return None
    common = fund_dr.index.intersection(bench_dr.index)
    if len(common) < 60:
        return None
    fund_ann = float(fund_dr.loc[common].mean() * TRADING_DAYS_PER_YEAR)
    bench_ann = float(bench_dr.loc[common].mean() * TRADING_DAYS_PER_YEAR)
    return fund_ann - (RISK_FREE_RATE_ANNUAL + b * (bench_ann - RISK_FREE_RATE_ANNUAL))


def compute_all_risk(nav_series: pd.Series, benchmark_series: pd.Series | None = None) -> dict:
    """Compute all risk metrics for a fund.

    Returns dict with keys: volatility, sharpe, sortino, max_drawdown, beta, alpha.
    """
    result = {}
    v = volatility(nav_series)
    if v is not None:
        result["volatility"] = v
    s = sharpe_ratio(nav_series)
    if s is not None:
        result["sharpe"] = s
    so = sortino_ratio(nav_series)
    if so is not None:
        result["sortino"] = so
    md = max_drawdown(nav_series)
    if md is not None:
        result["max_drawdown"] = md

    if benchmark_series is not None and not benchmark_series.empty:
        b = beta(nav_series, benchmark_series)
        if b is not None:
            result["beta"] = b
        a = alpha(nav_series, benchmark_series)
        if a is not None:
            result["alpha"] = a

    return result


def _trim_daily_returns(nav_series: pd.Series, years: int = 3) -> pd.Series | None:
    """Get daily returns for the last N years."""
    if nav_series.empty:
        return None
    end = nav_series.index[-1]
    start = end - pd.Timedelta(days=years * 365)
    trimmed = nav_series[nav_series.index >= start]
    if len(trimmed) < 60:
        return None
    return daily_returns(trimmed)
