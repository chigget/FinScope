
from datetime import date
from math import isfinite


def generate_insights(rows):
    """Generate financial insights from annual records."""

    if not rows:
        return [{
            "level": "info",
            "title": "No financial data",
            "message": "Add annual financial records first."
        }]

    clean = []

    # ===== Validate input data =====

    for row in rows:
        try:
            period_end = date.fromisoformat(
                str(row["period_end"])
            )
            revenue = float(row["revenue"])
            net_income = float(row["net_income"])

        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(
                "Invalid financial record"
            ) from error

        if (
            not isfinite(revenue)
            or not isfinite(net_income)
            or revenue <= 0
        ):
            raise ValueError(
                "Financial values must be finite; "
                "revenue must be positive"
            )

        clean.append({
            "period_end": period_end,
            "revenue": revenue,
            "net_income": net_income
        })

    clean.sort(key=lambda r: r["period_end"])

    if len({r["period_end"] for r in clean}) != len(clean):
        raise ValueError("Duplicate financial reporting period")

    latest = clean[-1]

    latest_margin = (
        latest["net_income"] / latest["revenue"] * 100
    )

    insights = [{
        "level": "info",
        "title": f"Net profit margin: {latest_margin:.2f}%",
        "message": (
            f"For the year ended {latest['period_end']}, "
            f"net income was ${latest['net_income'] / 1e9:.2f}B "
            f"on revenue of ${latest['revenue'] / 1e9:.2f}B."
        )
    }]

    if len(clean) == 1:
        insights.append({
            "level": "info",
            "title": "Not enough history for a trend",
            "message": (
                "At least two annual records are needed "
                "for a year-over-year comparison."
            )
        })
        return insights

    # ===== Detect reporting gaps =====

    gaps = []

    for previous, current in zip(clean, clean[1:]):

        days = (
            current["period_end"]
            - previous["period_end"]
        ).days

        if not 330 <= days <= 400:
            gaps.append((previous, current))

            insights.append({
                "level": "warning",
                "title": "Reporting-period gap",
                "message": (
                    f"The period ends {previous['period_end']} "
                    f"and {current['period_end']} are not "
                    "approximately one year apart. "
                    "Comparisons spanning this gap are "
                    "not treated as annual growth."
                )
            })

    # ===== Revenue Growth =====

    previous = clean[-2]

    recent_days = (
        latest["period_end"]
        - previous["period_end"]
    ).days

    if 330 <= recent_days <= 400:

        growth = (
            latest["revenue"] / previous["revenue"] - 1
        ) * 100

        previous_margin = (
            previous["net_income"]
            / previous["revenue"] * 100
        )

        margin_change = latest_margin - previous_margin

        insights.append({
            "level": "info",
            "title": f"Revenue growth: {growth:+.2f}%",
            "message": (
                f"Revenue changed from "
                f"${previous['revenue'] / 1e9:.2f}B "
                f"to ${latest['revenue'] / 1e9:.2f}B "
                f"between {previous['period_end']} "
                f"and {latest['period_end']}."
            )
        })

        # ===== Profit Margin Change =====

        insights.append({
            "level": "info",
            "title": (
                f"Net margin change: "
                f"{margin_change:+.2f} percentage points"
            ),
            "message": (
                f"Net margin moved from "
                f"{previous_margin:.2f}% to "
                f"{latest_margin:.2f}% over "
                "the same reporting periods."
            )
        })

    # ===== Long-Term CAGR =====

    if len(clean) >= 3 and not gaps:

        first = clean[0]

        years = (
            latest["period_end"] - first["period_end"]
        ).days / 365.2425

        cagr = (
            (latest["revenue"] / first["revenue"])
            ** (1 / years) - 1
        ) * 100

        insights.append({
            "level": "info",
            "title": f"Revenue CAGR: {cagr:+.2f}%",
            "message": (
                f"Revenue grew from "
                f"${first['revenue'] / 1e9:.2f}B "
                f"to ${latest['revenue'] / 1e9:.2f}B "
                f"over approximately {years:.1f} years. "
                "CAGR summarizes historical growth, "
                "not a forecast."
            )
        })

    return insights
