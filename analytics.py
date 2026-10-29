
from datetime import date

from normalizer import (
    get_annual_records,
    normalize_revenue
)


def analyze_company(data):

    financial_data = data["facts"]["us-gaap"]

    # 1. Extract annual revenue
    revenue_data = normalize_revenue(
        financial_data
    )

    # 2. Extract annual net income
    net_income_data = get_annual_records(
        financial_data,
        "NetIncomeLoss"
    )

    # 3. Match exact reporting periods
    common_periods = sorted(
        set(revenue_data) & set(net_income_data),
        key=lambda period: period[1]
    )[-6:]

    if len(common_periods) < 2:
        raise ValueError(
            "Not enough comparable annual data"
        )

    history = []

    # 4. Calculate financial metrics
    for start, end in common_periods:

        revenue_record = revenue_data[(start, end)]
        income_record = net_income_data[(start, end)]

        revenue = revenue_record["val"]
        net_income = income_record["val"]

        if revenue <= 0:
            raise ValueError(
                f"Invalid revenue for {end}"
            )

        profit_margin = (
            net_income / revenue * 100
        )

        # 5. Calculate YoY revenue growth
        growth = None

        if history:

            previous = history[-1]

            previous_end = date.fromisoformat(
                previous["period_end"]
            )

            current_end = date.fromisoformat(end)

            gap_days = (
                current_end - previous_end
            ).days

            # Only calculate annual growth
            # for approximately consecutive years
            if 330 <= gap_days <= 400:

                previous_revenue = (
                    previous["revenue"]
                )

                growth = (
                    revenue / previous_revenue - 1
                ) * 100

        # 6. Save annual record
        history.append({
            "year": int(end[:4]),
            "period_start": start,
            "period_end": end,

            "revenue": revenue,
            "net_income": net_income,

            "profit_margin": profit_margin,
            "revenue_growth": growth,

            "revenue_filing": revenue_record["accn"],
            "net_income_filing": income_record["accn"],

            "revenue_tag": revenue_record["xbrl_tag"],
            "revenue_filed": revenue_record["filed"],

            "net_income_tag": "NetIncomeLoss",
            "net_income_filed": income_record["filed"]
        })

    # Return the latest 5 annual records
    return history[-5:]
