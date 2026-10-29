
from datetime import date
from math import isclose, isfinite
import re


def validate_financial_data(results):

    if not results:
        raise ValueError("Financial data is empty")

    warnings = []
    previous = None
    seen_periods = set()

    for row in results:

        # 1. Check required fields
        required_fields = [
            "year",
            "period_end",
            "revenue",
            "net_income",
            "profit_margin",
            "revenue_growth",
            "revenue_filing",
            "net_income_filing"
        ]

        for field in required_fields:
            if field not in row:
                raise ValueError(
                    f"Missing required field: {field}"
                )

        # 2. Validate reporting date
        period = row["period_end"]

        try:
            period_date = date.fromisoformat(period)
        except (ValueError, TypeError):
            raise ValueError(
                f"Invalid reporting date: {period}"
            )

        if int(row["year"]) != period_date.year:
            raise ValueError(
                "Fiscal year does not match period end"
            )

        if period in seen_periods:
            raise ValueError(
                f"Duplicate period: {period}"
            )

        seen_periods.add(period)

        # 3. Validate financial values
        revenue = row["revenue"]
        net_income = row["net_income"]

        for name, value in [
            ("revenue", revenue),
            ("net_income", net_income),
            ("profit_margin", row["profit_margin"])
        ]:
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not isfinite(value)
            ):
                raise ValueError(
                    f"Invalid {name}: {value}"
                )

        if revenue <= 0:
            raise ValueError(
                f"Invalid revenue: {revenue}"
            )

        # 4. Validate profit margin
        expected_margin = (
            net_income / revenue * 100
        )

        if not isclose(
            expected_margin,
            row["profit_margin"],
            abs_tol=0.01
        ):
            raise ValueError(
                f"Incorrect profit margin for {period}"
            )

        # 5. Validate revenue growth
        growth = row["revenue_growth"]

        if growth is not None:
            if (
                isinstance(growth, bool)
                or not isinstance(growth, (int, float))
                or not isfinite(growth)
            ):
                raise ValueError(
                    f"Invalid growth for {period}"
                )

        # Only compare when there is a previous record
        if previous is not None:

            previous_date = date.fromisoformat(
                previous["period_end"]
            )

            days = (
                period_date - previous_date
            ).days

            if days <= 0:
                raise ValueError(
                    "Periods are not chronological"
                )

            # Missing or unusual annual period
            if not 330 <= days <= 400:

                warnings.append(
                    f"Unusual reporting gap before {period}"
                )

                if growth is not None:
                    raise ValueError(
                        "Revenue growth must be None "
                        f"across reporting gap: {period}"
                    )

            # Consecutive annual periods
            else:

                expected_growth = (
                    (revenue - previous["revenue"])
                    / previous["revenue"] * 100
                )

                if growth is None or not isclose(
                    expected_growth,
                    growth,
                    abs_tol=0.01
                ):
                    raise ValueError(
                        f"Incorrect revenue growth for {period}"
                    )

        # 6. Check SEC filing references
        for field in [
            "revenue_filing",
            "net_income_filing"
        ]:

            accession = row[field]

            if (
                not isinstance(accession, str)
                or not re.fullmatch(
                    r"\d{10}-\d{2}-\d{6}",
                    accession
                )
            ):
                warnings.append(
                    "Missing or invalid SEC filing "
                    f"reference: {period}"
                )

        if (
            row["revenue_filing"]
            != row["net_income_filing"]
        ):
            warnings.append(
                "Revenue and income use "
                f"different filings: {period}"
            )

        previous = row

    return warnings
