
from datetime import date


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


def analyze_company(data):
    financial_data = data["facts"]["us-gaap"]

    revenue_tags = [
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "Revenues",
        "SalesRevenueNet"
    ]

    revenue_data = {}

    for tag in revenue_tags:
        revenue_data = get_annual_records(
            financial_data, tag
        )

        if revenue_data:
            break

    net_income_data = get_annual_records(
        financial_data, "NetIncomeLoss"
    )

    common_periods = set(revenue_data) & set(net_income_data)

    periods = sorted(
        common_periods,
        key=lambda period: period[1]
    )[-6:]

    if len(periods) < 2:
        raise ValueError("Not enough annual financial data")

    history = []

    for start, end in periods:
        revenue_record = revenue_data[(start, end)]
        income_record = net_income_data[(start, end)]

        revenue = revenue_record["val"]
        net_income = income_record["val"]

        if revenue <= 0:
            raise ValueError(f"Invalid revenue: {end}")

        profit_margin = net_income / revenue * 100

        growth = None

        if history:
            previous_revenue = history[-1]["revenue"]

            growth = (
                (revenue - previous_revenue)
                / previous_revenue * 100
            )

        history.append({
            "year": int(end[:4]),
            "period_end": end,
            "revenue": revenue,
            "net_income": net_income,
            "profit_margin": profit_margin,
            "revenue_growth": growth,
            "revenue_filing": revenue_record.get("accn"),
            "net_income_filing": income_record.get("accn")
        })

    return history[-5:]
