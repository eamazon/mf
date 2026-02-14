"""Curated lists of popular Indian mutual fund categories and well-known scheme codes.

This provides a starting point for users who don't know specific scheme codes.
Categories follow SEBI's classification.
"""

# Major SEBI categories for equity funds
EQUITY_CATEGORIES = [
    "Large Cap",
    "Mid Cap",
    "Small Cap",
    "Large & Mid Cap",
    "Flexi Cap",
    "Multi Cap",
    "Value",
    "ELSS (Tax Saving)",
    "Focused",
    "Sectoral/Thematic",
]

DEBT_CATEGORIES = [
    "Liquid",
    "Ultra Short Duration",
    "Short Duration",
    "Medium Duration",
    "Corporate Bond",
    "Banking and PSU",
    "Gilt",
    "Dynamic Bond",
]

HYBRID_CATEGORIES = [
    "Aggressive Hybrid",
    "Conservative Hybrid",
    "Balanced Advantage",
    "Equity Savings",
]

# Keywords to match MFAPI scheme_category strings to our simplified categories
CATEGORY_KEYWORDS = {
    "Large Cap": ["large cap fund"],
    "Mid Cap": ["mid cap fund"],
    "Small Cap": ["small cap fund"],
    "Large & Mid Cap": ["large & mid cap"],
    "Flexi Cap": ["flexi cap"],
    "Multi Cap": ["multi cap"],
    "Value": ["value fund", "contra fund"],
    "ELSS (Tax Saving)": ["elss"],
    "Focused": ["focused fund"],
    "Sectoral/Thematic": ["sectoral", "thematic"],
    "Liquid": ["liquid fund"],
    "Ultra Short Duration": ["ultra short"],
    "Short Duration": ["short duration"],
    "Medium Duration": ["medium duration"],
    "Corporate Bond": ["corporate bond"],
    "Banking and PSU": ["banking and psu", "banking & psu"],
    "Gilt": ["gilt fund"],
    "Dynamic Bond": ["dynamic bond"],
    "Aggressive Hybrid": ["aggressive hybrid"],
    "Conservative Hybrid": ["conservative hybrid"],
    "Balanced Advantage": ["balanced advantage", "dynamic asset allocation"],
    "Equity Savings": ["equity savings"],
    "Index Fund": ["index fund", "index-"],
}

# Well-known Direct Growth schemes by category for quick recommendations.
# These are some of the most tracked funds - not recommendations, just a starting universe.
POPULAR_SCHEMES = {
    "Large Cap": [
        (120503, "Mirae Asset Large Cap Fund - Direct Growth"),
        (120505, "Canara Robeco Bluechip Equity Fund - Direct Growth"),
        (120586, "ICICI Prudential Bluechip Fund - Direct Growth"),
        (118989, "Axis Bluechip Fund - Direct Growth"),
        (100526, "SBI Blue Chip Fund - Direct Growth"),
    ],
    "Flexi Cap": [
        (122639, "Parag Parikh Flexi Cap Fund - Direct Growth"),
        (135802, "PGIM India Flexi Cap Fund - Direct Growth"),
        (120716, "UTI Flexi Cap Fund - Direct Growth"),
        (119714, "Kotak Flexicap Fund - Direct Growth"),
        (125354, "JM Flexicap Fund - Direct Growth"),
    ],
    "Mid Cap": [
        (131542, "Quant Mid Cap Fund - Direct Growth"),
        (120504, "Motilal Oswal Midcap Fund - Direct Growth"),
        (119748, "Kotak Emerging Equity Fund - Direct Growth"),
        (118994, "Axis Midcap Fund - Direct Growth"),
        (120587, "HDFC Mid-Cap Opportunities Fund - Direct Growth"),
    ],
    "Small Cap": [
        (125497, "Quant Small Cap Fund - Direct Growth"),
        (120828, "Nippon India Small Cap Fund - Direct Growth"),
        (130503, "Axis Small Cap Fund - Direct Growth"),
        (125307, "SBI Small Cap Fund - Direct Growth"),
        (119775, "Kotak Small Cap Fund - Direct Growth"),
    ],
    "ELSS (Tax Saving)": [
        (120847, "Mirae Asset Tax Saver Fund - Direct Growth"),
        (131595, "Quant Tax Plan - Direct Growth"),
        (119773, "Kotak Tax Saver Fund - Direct Growth"),
        (120587, "Canara Robeco Equity Tax Saver - Direct Growth"),
        (118988, "Axis Long Term Equity Fund - Direct Growth"),
    ],
    "Index Fund": [
        (120716, "UTI Nifty 50 Index Fund - Direct Growth"),
        (140420, "Navi Nifty 50 Index Fund - Direct Growth"),
        (122639, "HDFC Index Fund - Nifty 50 Plan - Direct Growth"),
        (135802, "Motilal Oswal Nifty 500 Index Fund - Direct Growth"),
    ],
    "Balanced Advantage": [
        (119568, "ICICI Prudential Balanced Advantage Fund - Direct Growth"),
        (120578, "HDFC Balanced Advantage Fund - Direct Growth"),
        (118997, "Edelweiss Balanced Advantage Fund - Direct Growth"),
    ],
}

# Nifty 50 TRI (Total Return Index) can be approximated using a Nifty 50 index fund
# This is used as benchmark for beta/alpha calculations
NIFTY50_INDEX_SCHEME = 120716  # UTI Nifty 50 Index Fund - Direct Growth


def classify_scheme(scheme_category: str) -> str | None:
    """Map an MFAPI scheme_category string to our simplified category."""
    if not scheme_category:
        return None
    cat_lower = scheme_category.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in cat_lower:
                return category
    return None
