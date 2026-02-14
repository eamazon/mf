"""Client for mf.captnemo.in - free fund metadata API (sourced from Kuvera)."""

import requests
from . import cache

BASE = "https://mf.captnemo.in"
SESSION = requests.Session()
SESSION.headers["User-Agent"] = "mf-recommender/0.1"


def get_fund_metadata(isin: str) -> dict | None:
    """Fetch fund metadata by ISIN from Kuvera/Captnemo API.

    Returns dict with keys like:
        fund_house, scheme_category, expense_ratio, aum, fund_manager,
        minimum_investment, etc.
    Returns None if the fund is not found.
    """
    key = f"kuvera_{isin}"
    cached = cache.get(key)
    if cached:
        return cached
    try:
        resp = SESSION.get(f"{BASE}/kuvera/{isin}", timeout=15)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        data = resp.json()
        cache.put(key, data)
        return data
    except (requests.RequestException, ValueError):
        return None
