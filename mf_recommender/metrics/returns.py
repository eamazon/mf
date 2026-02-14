"""Return calculations from NAV time series."""

import pandas as pd
import numpy as np
from datetime import timedelta


def absolute_return(nav_series: pd.Series, years: float) -> float | None:
    """Calculate absolute return over the last N years.

    Args:
        nav_series: Series with DatetimeIndex and float NAV values (sorted ascending).
        years: Number of years to look back.

    Returns:
        Absolute return as a decimal (0.15 = 15%), or None if insufficient data.
    """
    if nav_series.empty:
        return None
    end_date = nav_series.index[-1]
    start_date = end_date - timedelta(days=int(years * 365.25))
    # Find nearest available date to the target start
    mask = nav_series.index >= start_date
    if not mask.any():
        return None
    available = nav_series[mask]
    if available.empty or len(available) < 2:
        return None
    start_nav = available.iloc[0]
    end_nav = nav_series.iloc[-1]
    if start_nav <= 0:
        return None
    return (end_nav / start_nav) - 1


def cagr(nav_series: pd.Series, years: float) -> float | None:
    """Compound Annual Growth Rate over the last N years.

    This is the annualized return - the most standard way to compare fund performance.
    """
    abs_ret = absolute_return(nav_series, years)
    if abs_ret is None:
        return None
    total = 1 + abs_ret
    if total <= 0:
        return None
    return total ** (1 / years) - 1


def rolling_returns(nav_series: pd.Series, window_years: float = 1.0, step_days: int = 30) -> pd.Series:
    """Calculate rolling returns over a window, sampled every step_days.

    Useful for consistency analysis. Returns a Series of returns.
    """
    if nav_series.empty:
        return pd.Series(dtype=float)
    window_days = int(window_years * 365.25)
    results = []
    dates = []
    for i in range(window_days, len(nav_series), step_days):
        end_nav = nav_series.iloc[i]
        start_nav = nav_series.iloc[i - window_days] if (i - window_days) >= 0 else nav_series.iloc[0]
        if start_nav > 0:
            ret = (end_nav / start_nav) - 1
            results.append(ret)
            dates.append(nav_series.index[i])
    return pd.Series(results, index=dates)


def daily_returns(nav_series: pd.Series) -> pd.Series:
    """Calculate daily percentage returns from NAV series."""
    return nav_series.pct_change().dropna()


def compute_all_returns(nav_series: pd.Series) -> dict:
    """Compute a full set of return metrics.

    Returns dict with keys like return_1y, return_3y, return_5y, cagr_3y, etc.
    """
    result = {}
    for period, years in [("1y", 1), ("3y", 3), ("5y", 5), ("10y", 10)]:
        abs_r = absolute_return(nav_series, years)
        if abs_r is not None:
            result[f"return_{period}"] = abs_r
        c = cagr(nav_series, years) if years > 1 else abs_r
        if c is not None:
            result[f"cagr_{period}"] = c

    # Consistency: % of rolling 1-year periods with positive returns (over last 5 years)
    nav_5y = nav_series[nav_series.index >= nav_series.index[-1] - timedelta(days=5 * 365)] if len(nav_series) > 365 else nav_series
    rolling = rolling_returns(nav_5y, window_years=1.0, step_days=30)
    if len(rolling) > 0:
        result["consistency"] = (rolling > 0).mean()

    return result
