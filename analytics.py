

from normalizer import (
    get_annual_records,
    normalize_revenue
)


def analyze_company(data):

    financial_data = data["facts"]["us-gaap"]

    # Normalize revenue across reporting years
    revenue_data = normalize_revenue(financial_data)

    # Extract net income
    net_income_data = get_annual_records(
        financial_data,
        "NetIncomeLoss"
    )

    # Match exact reporting periods
    common_periods = sorted(
        set(revenue_data) & set(net_income_data),
        key=lambda period: period[1]
    )[-6:]

    if len(common_periods) < 2:
        raise ValueError(
            "Not enough comparable annual data"
        )

    history = []

    for start, end in common_periods:

        revenue_record = revenue_data[(start, end)]
        income_record = net_income_data[(start, end)]

        revenue = revenue_record["val"]
        net_income = income_record["val"]

        if revenue <= 0:
            raise ValueError(
                f"Invalid revenue for {end}"
            )

        # Calculate YoY revenue growth
        growth = None

        if history:
            previous_revenue = history[-1]["revenue"]

            growth = (
                revenue / previous_revenue - 1
            ) * 100

        # Preserve both values and source metadata
        history.append({
            "year": int(end[:4]),
            "period_start": start,
            "period_end": end,

            "revenue": revenue,
            "net_income": net_income,

            "profit_margin": (
                net_income / revenue * 100
            ),
            "revenue_growth": growth,

            "revenue_filing": revenue_record["accn"],
            "net_income_filing": income_record["accn"],

            "revenue_tag": revenue_record["xbrl_tag"],
            "revenue_filed": revenue_record["filed"],

            "net_income_tag": "NetIncomeLoss",
            "net_income_filed": income_record["filed"]
        })

    return history[-5:]
