
from datetime import date


# ===== Extract Annual Financial Records =====

def get_annual_records(financial_data, metric):

    if metric not in financial_data:
        return {}

    records = financial_data[metric]["units"].get("USD", [])

    annual_data = {}

    for record in records:

        if record.get("form") != "10-K":
            continue

        if record.get("fp") != "FY":
            continue

        required = ("start", "end", "filed", "val")

        if not all(k in record for k in required):
            continue

        start = date.fromisoformat(record["start"])
        end = date.fromisoformat(record["end"])

        duration = (end - start).days

        if not 330 <= duration <= 390:
            continue

        period = (record["start"], record["end"])

        previous = annual_data.get(period)

        if previous is None or record["filed"] > previous["filed"]:
            annual_data[period] = record

    return annual_data


# ===== Analyze Company Financial Data =====

def analyze_company(data):

    financial_data = data["facts"]["us-gaap"]

    # Common Revenue XBRL Tags
    revenue_tags = [
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "Revenues",
        "SalesRevenueNet"
    ]

    revenue_data = {}
    revenue_tag = None

    # Find available Revenue tag
    for tag in revenue_tags:

        revenue_data = get_annual_records(
            financial_data, tag
        )

        if revenue_data:
            revenue_tag = tag
            break

    # Extract Net Income
    net_income_data = get_annual_records(
        financial_data, "NetIncomeLoss"
    )

    # Match financial reporting periods
    common_periods = set(revenue_data) & set(net_income_data)

    periods = sorted(
        common_periods,
        key=lambda period: period[1]
    )[-6:]

    if len(periods) < 2:
        raise ValueError(
            "Not enough annual financial data"
        )

    history = []

    # ===== Calculate Financial Metrics =====

    for start, end in periods:

        revenue_record = revenue_data[(start, end)]
        income_record = net_income_data[(start, end)]

        revenue = revenue_record["val"]
        net_income = income_record["val"]

        if revenue <= 0:
            raise ValueError(
                f"Invalid revenue: {end}"
            )

        # Calculate Profit Margin
        profit_margin = net_income / revenue * 100

        # Calculate YoY Revenue Growth
        growth = None

        if history:

            previous_revenue = history[-1]["revenue"]

            if previous_revenue > 0:
                growth = (
                    (revenue - previous_revenue)
                    / previous_revenue * 100
                )

        # Save financial metrics and provenance
        history.append({
            "year": int(end[:4]),
            "period_start": start,
            "period_end": end,

            "revenue": revenue,
            "net_income": net_income,

            "profit_margin": profit_margin,
            "revenue_growth": growth,

            # SEC Filing References
            "revenue_filing": revenue_record.get("accn"),
            "net_income_filing": income_record.get("accn"),

            # SEC Data Provenance
            "revenue_tag": revenue_tag,
            "revenue_filed": revenue_record["filed"],

            "net_income_tag": "NetIncomeLoss",
            "net_income_filed": income_record["filed"]
        })

    # Return most recent 5 years
    return history[-5:]
