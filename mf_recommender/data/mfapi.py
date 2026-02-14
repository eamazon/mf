"""Client for MFAPI.in - free NAV history API for Indian mutual funds."""

import requests
import pandas as pd
from datetime import datetime

from . import cache

BASE = "https://api.mfapi.in/mf"
SESSION = requests.Session()
SESSION.headers["User-Agent"] = "mf-recommender/0.1"


def get_all_schemes() -> list[dict]:
    """Return list of all schemes: [{schemeCode, schemeName, ...}]."""
    cached = cache.get("all_schemes")
    if cached:
        return cached
    resp = SESSION.get(BASE, timeout=30)
    resp.raise_for_status()
    schemes = resp.json()
    cache.put("all_schemes", schemes)
    return schemes


def search_schemes(query: str) -> list[dict]:
    """Search schemes by name (case-insensitive substring match)."""
    query_lower = query.lower()
    return [
        s for s in get_all_schemes()
        if query_lower in s.get("schemeName", "").lower()
    ]


def get_scheme_nav(scheme_code: int) -> dict:
    """Fetch full historical NAV + metadata for a scheme.

    Returns: {"meta": {...}, "data": [{"date": "dd-mm-yyyy", "nav": "123.45"}, ...]}
    """
    key = f"nav_{scheme_code}"
    cached = cache.get(key, ttl=12 * 3600)  # 12 hour cache for NAV
    if cached:
        return cached
    resp = SESSION.get(f"{BASE}/{scheme_code}", timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if data.get("status") != "SUCCESS":
        raise ValueError(f"MFAPI returned status={data.get('status')} for scheme {scheme_code}")
    cache.put(key, data)
    return data


def get_nav_dataframe(scheme_code: int) -> pd.DataFrame:
    """Return NAV history as a pandas DataFrame with date index and float nav column.

    Sorted ascending by date (oldest first).
    """
    raw = get_scheme_nav(scheme_code)
    rows = raw["data"]
    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"], format="%d-%m-%Y")
    df["nav"] = pd.to_numeric(df["nav"], errors="coerce")
    df = df.dropna(subset=["nav"])
    df = df.sort_values("date").reset_index(drop=True)
    df = df.set_index("date")
    return df


def get_scheme_meta(scheme_code: int) -> dict:
    """Return just the metadata portion for a scheme."""
    raw = get_scheme_nav(scheme_code)
    return raw.get("meta", {})
