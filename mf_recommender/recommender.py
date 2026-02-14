"""Core recommendation engine - fetches data, computes metrics, ranks funds."""

from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd

from .data import mfapi, kuvera
from .data.fund_categories import POPULAR_SCHEMES, NIFTY50_INDEX_SCHEME, classify_scheme
from .metrics.returns import compute_all_returns
from .metrics.risk import compute_all_risk
from .metrics.scoring import compute_composite_score, score_label


def analyze_fund(scheme_code: int, benchmark_nav: pd.Series | None = None) -> dict | None:
    """Analyze a single fund: fetch data, compute all metrics, score it.

    Returns a dict with all metrics + composite_score, or None on failure.
    """
    try:
        nav_df = mfapi.get_nav_dataframe(scheme_code)
    except Exception:
        return None

    if nav_df.empty or len(nav_df) < 60:
        return None

    nav = nav_df["nav"]
    meta = mfapi.get_scheme_meta(scheme_code)

    # Compute returns
    ret = compute_all_returns(nav)

    # Compute risk
    risk = compute_all_risk(nav, benchmark_nav)

    # Merge all metrics
    metrics = {**ret, **risk}

    # Try to get extra metadata from Kuvera
    isin = meta.get("isin_growth") or meta.get("isin_div_reinvestment")
    kuvera_data = {}
    if isin:
        raw = kuvera.get_fund_metadata(isin)
        if isinstance(raw, dict):
            kuvera_data = raw
        elif isinstance(raw, list) and raw and isinstance(raw[0], dict):
            kuvera_data = raw[0]

    # Kuvera provides expense_ratio as a percentage (e.g. 0.64 means 0.64%)
    expense = kuvera_data.get("expense_ratio")
    if expense is not None:
        try:
            val = float(expense)
            if val > 0:
                metrics["expense_ratio"] = val  # Already in percentage form
        except (ValueError, TypeError):
            pass

    aum = kuvera_data.get("aum")
    if aum is not None:
        try:
            val = float(aum)
            if val > 0:
                metrics["aum"] = val
        except (ValueError, TypeError):
            pass

    # Composite score
    metrics["composite_score"] = compute_composite_score(metrics)
    metrics["score_label"] = score_label(metrics["composite_score"])

    # Attach metadata
    result = {
        "scheme_code": scheme_code,
        "scheme_name": meta.get("scheme_name", f"Scheme {scheme_code}"),
        "fund_house": meta.get("fund_house", kuvera_data.get("fund_house", "Unknown")),
        "category": classify_scheme(meta.get("scheme_category", "")) or meta.get("scheme_category", ""),
        "fund_manager": kuvera_data.get("fund_manager", "N/A"),
        "isin": isin or "N/A",
        **metrics,
    }
    return result


def get_benchmark_nav() -> pd.Series | None:
    """Fetch Nifty 50 index fund NAV as benchmark."""
    try:
        df = mfapi.get_nav_dataframe(NIFTY50_INDEX_SCHEME)
        return df["nav"]
    except Exception:
        return None


def recommend_category(category: str, top_n: int = 5, progress_callback=None) -> list[dict]:
    """Get top N fund recommendations for a given category.

    Args:
        category: Category name (must be a key in POPULAR_SCHEMES).
        top_n: Number of top funds to return.
        progress_callback: Optional callable(done, total) for progress updates.

    Returns:
        List of fund analysis dicts, sorted by composite_score descending.
    """
    schemes = POPULAR_SCHEMES.get(category, [])
    if not schemes:
        return []

    # Fetch benchmark once
    benchmark = get_benchmark_nav()

    results = []
    total = len(schemes)

    def _analyze(code_name):
        code, name = code_name
        return analyze_fund(code, benchmark)

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(_analyze, s): s for s in schemes}
        done = 0
        for future in as_completed(futures):
            done += 1
            if progress_callback:
                progress_callback(done, total)
            result = future.result()
            if result:
                results.append(result)

    results.sort(key=lambda x: x.get("composite_score", 0), reverse=True)
    return results[:top_n]


def recommend_all_categories(top_n: int = 3, progress_callback=None) -> dict[str, list[dict]]:
    """Get top recommendations across all major categories.

    Returns dict mapping category name to list of fund analysis dicts.
    """
    all_results = {}
    categories = list(POPULAR_SCHEMES.keys())
    total_schemes = sum(len(v) for v in POPULAR_SCHEMES.values())
    done_total = 0

    benchmark = get_benchmark_nav()

    for cat in categories:
        schemes = POPULAR_SCHEMES[cat]
        cat_results = []
        for code, name in schemes:
            done_total += 1
            if progress_callback:
                progress_callback(done_total, total_schemes)
            result = analyze_fund(code, benchmark)
            if result:
                cat_results.append(result)

        cat_results.sort(key=lambda x: x.get("composite_score", 0), reverse=True)
        all_results[cat] = cat_results[:top_n]

    return all_results


def search_and_analyze(query: str, max_results: int = 10) -> list[dict]:
    """Search for funds by name and analyze the matches.

    Filters to Direct Growth plans only for cleaner results.
    """
    matches = mfapi.search_schemes(query)

    # Prefer direct growth plans
    direct_growth = [
        m for m in matches
        if "direct" in m.get("schemeName", "").lower()
        and "growth" in m.get("schemeName", "").lower()
    ]
    if direct_growth:
        matches = direct_growth

    matches = matches[:max_results]
    if not matches:
        return []

    benchmark = get_benchmark_nav()
    results = []

    for m in matches:
        code = m.get("schemeCode")
        if code:
            result = analyze_fund(int(code), benchmark)
            if result:
                results.append(result)

    results.sort(key=lambda x: x.get("composite_score", 0), reverse=True)
    return results
