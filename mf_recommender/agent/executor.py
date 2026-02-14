"""Executes tool calls from the Claude agent by dispatching to our analysis functions."""

import json
import math

from ..recommender import (
    analyze_fund,
    get_benchmark_nav,
    recommend_category,
    search_and_analyze,
)
from ..explain import explain, METRIC_EXPLANATIONS
from ..data.fund_categories import POPULAR_SCHEMES


def execute_tool(name: str, inputs: dict) -> str:
    """Dispatch a tool call to the right function and return JSON result."""
    try:
        if name == "recommend_by_category":
            return _recommend_by_category(inputs)
        elif name == "search_fund":
            return _search_fund(inputs)
        elif name == "analyze_fund":
            return _analyze_fund(inputs)
        elif name == "compare_funds":
            return _compare_funds(inputs)
        elif name == "calculate_goal":
            return _calculate_goal(inputs)
        elif name == "build_portfolio":
            return _build_portfolio(inputs)
        elif name == "explain_metric":
            return _explain_metric(inputs)
        elif name == "get_risk_profile":
            return _get_risk_profile(inputs)
        else:
            return json.dumps({"error": f"Unknown tool: {name}"})
    except Exception as e:
        return json.dumps({"error": str(e)})


def _recommend_by_category(inputs: dict) -> str:
    category = inputs["category"]
    top_n = inputs.get("top_n", 5)
    results = recommend_category(category, top_n=top_n)
    return json.dumps({"category": category, "funds": _simplify_funds(results)})


def _search_fund(inputs: dict) -> str:
    query = inputs["query"]
    max_results = inputs.get("max_results", 5)
    results = search_and_analyze(query, max_results=max_results)
    return json.dumps({"query": query, "funds": _simplify_funds(results)})


def _analyze_fund(inputs: dict) -> str:
    scheme_code = inputs["scheme_code"]
    benchmark = get_benchmark_nav()
    result = analyze_fund(scheme_code, benchmark)
    if not result:
        return json.dumps({"error": f"Could not analyze scheme {scheme_code}"})
    return json.dumps({"fund": _simplify_fund(result)})


def _compare_funds(inputs: dict) -> str:
    codes = inputs["scheme_codes"]
    benchmark = get_benchmark_nav()
    funds = []
    for code in codes:
        result = analyze_fund(code, benchmark)
        if result:
            funds.append(_simplify_fund(result))
    return json.dumps({"comparison": funds})


def _calculate_goal(inputs: dict) -> str:
    years = inputs["years"]
    target = inputs.get("target_amount")
    monthly = inputs.get("monthly_sip")
    cagr = inputs.get("expected_cagr", 0.12)
    monthly_rate = (1 + cagr) ** (1 / 12) - 1
    n_months = int(years * 12)

    result = {"years": years, "expected_cagr_pct": round(cagr * 100, 1)}

    if target and not monthly:
        # Calculate required monthly SIP
        if monthly_rate == 0:
            required = target / n_months
        else:
            required = target * monthly_rate / ((1 + monthly_rate) ** n_months - 1)
        result["target_amount"] = target
        result["required_monthly_sip"] = round(required, 0)
        result["total_invested"] = round(required * n_months, 0)
        result["wealth_gained"] = round(target - required * n_months, 0)
    elif monthly and not target:
        # Calculate expected corpus
        if monthly_rate == 0:
            corpus = monthly * n_months
        else:
            corpus = monthly * ((1 + monthly_rate) ** n_months - 1) / monthly_rate * (1 + monthly_rate)
        result["monthly_sip"] = monthly
        result["expected_corpus"] = round(corpus, 0)
        result["total_invested"] = round(monthly * n_months, 0)
        result["wealth_gained"] = round(corpus - monthly * n_months, 0)
    elif target and monthly:
        # Calculate both directions
        if monthly_rate == 0:
            corpus = monthly * n_months
            required = target / n_months
        else:
            corpus = monthly * ((1 + monthly_rate) ** n_months - 1) / monthly_rate * (1 + monthly_rate)
            required = target * monthly_rate / ((1 + monthly_rate) ** n_months - 1)
        result["with_given_sip"] = {
            "monthly_sip": monthly,
            "expected_corpus": round(corpus, 0),
            "total_invested": round(monthly * n_months, 0),
        }
        result["to_reach_target"] = {
            "target_amount": target,
            "required_monthly_sip": round(required, 0),
        }
    else:
        return json.dumps({"error": "Provide either target_amount or monthly_sip (or both)"})

    # Suggest which fund types might deliver this CAGR
    if cagr >= 0.15:
        result["suitable_categories"] = ["Small Cap", "Mid Cap", "Flexi Cap"]
        result["note"] = "15%+ CAGR needs equity-heavy allocation with higher risk."
    elif cagr >= 0.12:
        result["suitable_categories"] = ["Flexi Cap", "Large Cap", "Large & Mid Cap", "Index Fund"]
        result["note"] = "12-15% CAGR is realistic for diversified equity over 7+ years."
    elif cagr >= 0.08:
        result["suitable_categories"] = ["Balanced Advantage", "Aggressive Hybrid", "Large Cap"]
        result["note"] = "8-12% CAGR is achievable with balanced/hybrid funds."
    else:
        result["suitable_categories"] = ["Short Duration", "Corporate Bond", "Banking and PSU"]
        result["note"] = "Below 8% CAGR is debt territory - lower risk, lower return."

    return json.dumps(result)


def _build_portfolio(inputs: dict) -> str:
    risk = inputs["risk_tolerance"]
    horizon = inputs["investment_horizon_years"]
    budget = inputs["monthly_budget"]
    tax_saving = inputs.get("tax_saving_needed", False)

    # Determine allocation based on risk + horizon
    allocation = _get_allocation(risk, horizon, tax_saving)

    # For each category, get top fund
    portfolio = []
    total_allocated = 0
    for cat, pct in allocation.items():
        amount = round(budget * pct / 100)
        if amount < 500:
            continue
        funds = recommend_category(cat, top_n=1)
        fund_info = None
        if funds:
            f = funds[0]
            fund_info = {
                "scheme_code": f.get("scheme_code"),
                "scheme_name": f.get("scheme_name"),
                "composite_score": f.get("composite_score"),
                "cagr_3y": _pct(f.get("cagr_3y")),
                "sharpe": f.get("sharpe"),
            }
        portfolio.append({
            "category": cat,
            "allocation_pct": pct,
            "monthly_amount": amount,
            "recommended_fund": fund_info,
        })
        total_allocated += amount

    # Expected blended returns
    expected_cagr = _estimate_blended_cagr(risk, horizon)

    return json.dumps({
        "risk_tolerance": risk,
        "investment_horizon_years": horizon,
        "monthly_budget": budget,
        "portfolio": portfolio,
        "total_monthly_sip": total_allocated,
        "expected_cagr_range": expected_cagr,
        "rebalance_frequency": "Annual",
    })


def _explain_metric(inputs: dict) -> str:
    metric = inputs["metric"]
    info = METRIC_EXPLANATIONS.get(metric)
    if not info:
        return json.dumps({"error": f"Unknown metric: {metric}", "available": list(METRIC_EXPLANATIONS.keys())})
    return json.dumps(info)


def _get_risk_profile(inputs: dict) -> str:
    age = inputs["age"]
    stable = inputs["income_stable"]
    emergency = inputs.get("emergency_fund_months", 0)
    experience = inputs.get("investment_experience_years", 0)
    drop_reaction = inputs["comfort_with_30pct_drop"]

    score = 0

    # Age: younger = can take more risk
    if age < 30:
        score += 3
    elif age < 40:
        score += 2
    elif age < 50:
        score += 1

    # Income stability
    if stable:
        score += 2

    # Emergency fund
    if emergency >= 6:
        score += 2
    elif emergency >= 3:
        score += 1

    # Experience
    if experience >= 5:
        score += 2
    elif experience >= 2:
        score += 1

    # Behavioral
    if drop_reaction == "buy_more":
        score += 3
    elif drop_reaction == "worried_but_hold":
        score += 1
    # panic_sell adds 0

    # Classify
    if score >= 9:
        profile = "aggressive"
        desc = "You can handle high volatility for potentially higher long-term returns."
        categories = ["Small Cap", "Mid Cap", "Flexi Cap", "Sectoral/Thematic"]
    elif score >= 5:
        profile = "moderate"
        desc = "You prefer a balance between growth and stability."
        categories = ["Flexi Cap", "Large Cap", "Large & Mid Cap", "ELSS (Tax Saving)"]
    else:
        profile = "conservative"
        desc = "Capital preservation is your priority. You prefer steady, predictable returns."
        categories = ["Large Cap", "Balanced Advantage", "Index Fund", "Short Duration"]

    return json.dumps({
        "risk_profile": profile,
        "score": score,
        "max_score": 12,
        "description": desc,
        "recommended_categories": categories,
        "inputs": {
            "age": age,
            "income_stable": stable,
            "emergency_fund_months": emergency,
            "experience_years": experience,
            "drop_reaction": drop_reaction,
        },
    })


def _get_allocation(risk: str, horizon: int, tax_saving: bool) -> dict:
    """Determine category allocation percentages based on risk and horizon."""
    if risk == "aggressive":
        if horizon >= 7:
            alloc = {"Small Cap": 25, "Mid Cap": 25, "Flexi Cap": 30, "Index Fund": 20}
        elif horizon >= 4:
            alloc = {"Mid Cap": 25, "Flexi Cap": 30, "Large Cap": 25, "Index Fund": 20}
        else:
            alloc = {"Flexi Cap": 30, "Large Cap": 30, "Balanced Advantage": 20, "Index Fund": 20}
    elif risk == "moderate":
        if horizon >= 7:
            alloc = {"Flexi Cap": 30, "Large Cap": 25, "Mid Cap": 20, "Index Fund": 25}
        elif horizon >= 4:
            alloc = {"Large Cap": 30, "Flexi Cap": 30, "Balanced Advantage": 20, "Index Fund": 20}
        else:
            alloc = {"Large Cap": 30, "Balanced Advantage": 30, "Index Fund": 25, "Flexi Cap": 15}
    else:  # conservative
        if horizon >= 7:
            alloc = {"Large Cap": 30, "Index Fund": 30, "Balanced Advantage": 25, "Flexi Cap": 15}
        elif horizon >= 4:
            alloc = {"Large Cap": 25, "Index Fund": 30, "Balanced Advantage": 30, "Flexi Cap": 15}
        else:
            alloc = {"Index Fund": 35, "Balanced Advantage": 35, "Large Cap": 30}

    # Carve out ELSS if needed
    if tax_saving and "ELSS (Tax Saving)" not in alloc:
        # Take from the largest allocation
        largest = max(alloc, key=alloc.get)
        elss_pct = min(20, alloc[largest])
        alloc[largest] -= elss_pct
        alloc["ELSS (Tax Saving)"] = elss_pct

    return alloc


def _estimate_blended_cagr(risk: str, horizon: int) -> str:
    """Rough expected CAGR range based on risk profile and horizon."""
    if risk == "aggressive":
        return "13-18%" if horizon >= 7 else "10-15%"
    elif risk == "moderate":
        return "11-15%" if horizon >= 7 else "9-13%"
    else:
        return "8-12%" if horizon >= 7 else "7-10%"


def _simplify_funds(funds: list[dict]) -> list[dict]:
    return [_simplify_fund(f) for f in funds]


def _simplify_fund(f: dict) -> dict:
    """Extract key fields for agent consumption."""
    return {
        "scheme_code": f.get("scheme_code"),
        "scheme_name": f.get("scheme_name"),
        "fund_house": f.get("fund_house"),
        "category": f.get("category"),
        "composite_score": f.get("composite_score"),
        "score_label": f.get("score_label"),
        "cagr_1y": _pct(f.get("cagr_1y")),
        "cagr_3y": _pct(f.get("cagr_3y")),
        "cagr_5y": _pct(f.get("cagr_5y")),
        "sharpe": _round(f.get("sharpe")),
        "sortino": _round(f.get("sortino")),
        "volatility": _pct(f.get("volatility")),
        "max_drawdown": _pct(f.get("max_drawdown")),
        "consistency": _pct(f.get("consistency")),
        "beta": _round(f.get("beta")),
        "alpha": _pct(f.get("alpha")),
        "expense_ratio": f.get("expense_ratio"),
    }


def _pct(v):
    if v is None:
        return None
    return round(v * 100, 1)


def _round(v):
    if v is None:
        return None
    return round(v, 2)
