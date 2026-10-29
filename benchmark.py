
from datetime import date
from math import isfinite
from statistics import median


def build_peer_benchmark(company_histories):

    if len(company_histories) < 2:
        raise ValueError("Select at least two companies")

    yearly = {}

    # Group records by reporting-end year
    for company, records in company_histories.items():

        items = {}

        for row in records:
            period = str(row["period_end"])
            year = date.fromisoformat(period).year

            if year in items:
                raise ValueError(
                    f"Multiple records in {year} for {company}"
                )

            items[year] = row

        yearly[company] = items

    # Find years available for all companies
    common_years = set.intersection(
        *(set(items) for items in yearly.values())
    )

    if not common_years:
        raise ValueError(
            "Selected companies have no common reporting year"
        )

    comparison_year = max(common_years)
    rows = []

    for company, items in yearly.items():

        record = items[comparison_year]

        revenue = float(record["revenue"])
        net_income = float(record["net_income"])

        if (
            not isfinite(revenue)
            or not isfinite(net_income)
            or revenue <= 0
        ):
            raise ValueError(
                f"Invalid financial data for {company}"
            )

        margin = net_income / revenue * 100

        growth = record.get("revenue_growth")

        if growth is not None:
            growth = float(growth)

            if not isfinite(growth):
                growth = None

        rows.append({
            "Company": company,
            "Period End": str(record["period_end"]),
            "Revenue ($B)": revenue / 1e9,
            "Net Margin (%)": margin,
            "Revenue Growth (%)": growth
        })

    # Calculate peer medians
    margin_median = median(
        row["Net Margin (%)"] for row in rows
    )

    growth_values = [
        row["Revenue Growth (%)"]
        for row in rows
        if row["Revenue Growth (%)"] is not None
    ]

    growth_median = (
        median(growth_values)
        if growth_values else None
    )

    # Rank by profit margin
    ranked_margins = sorted(
        {row["Net Margin (%)"] for row in rows},
        reverse=True
    )

    for row in rows:

        row["Margin Rank"] = (
            ranked_margins.index(row["Net Margin (%)"]) + 1
        )

        row["Margin vs Median (pp)"] = (
            row["Net Margin (%)"] - margin_median
        )

        row["Growth vs Median (pp)"] = (
            row["Revenue Growth (%)"] - growth_median
            if growth_median is not None
            and row["Revenue Growth (%)"] is not None
            else None
        )

    rows.sort(key=lambda row: row["Margin Rank"])

    return {
        "year": comparison_year,
        "rows": rows,
        "median_margin": margin_median,
        "median_growth": growth_median
    }
