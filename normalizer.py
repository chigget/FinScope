
from datetime import date


# ===== Revenue XBRL Tags =====

REVENUE_TAGS = [
    "RevenueFromContractWithCustomerExcludingAssessedTax",
    "Revenues",
    "SalesRevenueNet"
]


# ===== Extract Annual Records =====

def get_annual_records(financial_data, tag):

    records = (
        financial_data
        .get(tag, {})
        .get("units", {})
        .get("USD", [])
    )

    annual = {}

    for record in records:

        if record.get("form") not in ("10-K", "10-K/A"):
            continue

        if record.get("fp") != "FY":
            continue

        required = ("start", "end", "filed", "val", "accn")

        if not all(field in record for field in required):
            continue

        try:
            start = date.fromisoformat(record["start"])
            end = date.fromisoformat(record["end"])
        except (ValueError, TypeError):
            continue

        duration = (end - start).days

        if not 330 <= duration <= 390:
            continue

        period = (record["start"], record["end"])
        previous = annual.get(period)

        if (
            previous is None
            or (record["filed"], record["accn"])
            > (previous["filed"], previous["accn"])
        ):
            annual[period] = record.copy()

    return annual


# ===== Normalize Revenue =====

def normalize_revenue(financial_data):

    selected = {}

    for tag in REVENUE_TAGS:

        records = get_annual_records(
            financial_data,
            tag
        )

        for period, record in records.items():

            if period not in selected:

                selected[period] = {
                    **record,
                    "xbrl_tag": tag
                }

    return selected
