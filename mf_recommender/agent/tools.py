"""Tool definitions for the Claude agent - wraps our analysis functions as callable tools."""

# -- Tool schemas for Anthropic tool_use --

TOOLS = [
    {
        "name": "recommend_by_category",
        "description": (
            "Get top-ranked mutual funds for a specific investment category. "
            "Categories: Large Cap, Mid Cap, Small Cap, Flexi Cap, ELSS (Tax Saving), "
            "Index Fund, Balanced Advantage, Value, Large & Mid Cap. "
            "Returns funds ranked by composite score with full metrics."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "Fund category name, e.g. 'Large Cap', 'Flexi Cap', 'ELSS (Tax Saving)'",
                },
                "top_n": {
                    "type": "integer",
                    "description": "Number of top funds to return (default 5)",
                    "default": 5,
                },
            },
            "required": ["category"],
        },
    },
    {
        "name": "search_fund",
        "description": (
            "Search for mutual funds by name and analyze them. "
            "Automatically filters to Direct Growth plans. "
            "Use this when the user mentions a specific fund name or AMC."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Fund name or partial name to search, e.g. 'parag parikh', 'hdfc mid cap'",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum results to analyze (default 5)",
                    "default": 5,
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "analyze_fund",
        "description": (
            "Deep analysis of a specific fund by its AMFI scheme code. "
            "Returns all metrics: returns (1y/3y/5y CAGR), risk (Sharpe, Sortino, "
            "volatility, max drawdown, beta, alpha), expense ratio, consistency, "
            "and composite score."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "scheme_code": {
                    "type": "integer",
                    "description": "AMFI scheme code number",
                },
            },
            "required": ["scheme_code"],
        },
    },
    {
        "name": "compare_funds",
        "description": (
            "Compare two or more funds side by side on all metrics. "
            "Provide scheme codes for each fund."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "scheme_codes": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": "List of AMFI scheme codes to compare",
                },
            },
            "required": ["scheme_codes"],
        },
    },
    {
        "name": "calculate_goal",
        "description": (
            "Calculate the required monthly SIP or expected corpus for a financial goal. "
            "Given a target amount, time horizon, and expected return rate, calculates "
            "the required monthly SIP. Or given a monthly SIP and time, calculates "
            "the expected corpus."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "target_amount": {
                    "type": "number",
                    "description": "Target corpus in rupees (e.g. 10000000 for 1 crore). Optional if calculating corpus.",
                },
                "monthly_sip": {
                    "type": "number",
                    "description": "Monthly SIP amount in rupees. Optional if calculating required SIP.",
                },
                "years": {
                    "type": "number",
                    "description": "Investment time horizon in years",
                },
                "expected_cagr": {
                    "type": "number",
                    "description": "Expected annual return as decimal (e.g. 0.12 for 12%). If not provided, uses 12% for equity.",
                },
            },
            "required": ["years"],
        },
    },
    {
        "name": "build_portfolio",
        "description": (
            "Build a diversified mutual fund portfolio based on investor profile. "
            "Takes risk tolerance, investment horizon, and monthly budget, "
            "then recommends a portfolio with allocation percentages and specific funds."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "risk_tolerance": {
                    "type": "string",
                    "enum": ["conservative", "moderate", "aggressive"],
                    "description": "Investor's risk tolerance level",
                },
                "investment_horizon_years": {
                    "type": "integer",
                    "description": "How many years the investor plans to stay invested",
                },
                "monthly_budget": {
                    "type": "number",
                    "description": "Monthly investment amount in rupees",
                },
                "tax_saving_needed": {
                    "type": "boolean",
                    "description": "Whether the investor needs ELSS for 80C tax saving",
                    "default": False,
                },
            },
            "required": ["risk_tolerance", "investment_horizon_years", "monthly_budget"],
        },
    },
    {
        "name": "explain_metric",
        "description": (
            "Explain a financial metric in plain English. "
            "Metrics: cagr_1y, cagr_3y, cagr_5y, sharpe, sortino, volatility, "
            "max_drawdown, beta, alpha, expense_ratio, aum, consistency, composite_score"
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "metric": {
                    "type": "string",
                    "description": "Metric key to explain",
                },
            },
            "required": ["metric"],
        },
    },
    {
        "name": "get_risk_profile",
        "description": (
            "Determine an investor's risk profile based on their answers. "
            "Takes age, income stability, existing savings, investment experience, "
            "and reaction to market drops to classify as conservative/moderate/aggressive."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "age": {"type": "integer", "description": "Investor's age"},
                "income_stable": {
                    "type": "boolean",
                    "description": "Whether the investor has a stable income (salaried/business)",
                },
                "emergency_fund_months": {
                    "type": "integer",
                    "description": "Months of expenses saved as emergency fund",
                },
                "investment_experience_years": {
                    "type": "integer",
                    "description": "Years of investment experience",
                },
                "comfort_with_30pct_drop": {
                    "type": "string",
                    "enum": ["panic_sell", "worried_but_hold", "buy_more"],
                    "description": "How the investor would react if their portfolio dropped 30%",
                },
            },
            "required": ["age", "income_stable", "emergency_fund_months", "comfort_with_30pct_drop"],
        },
    },
]
