
from normalizer import REVENUE_TAGS, get_annual_records


def analyze_data_quality(company_data, results):
    """Detect potential financial data quality issues."""

    issues = []
    gaap = company_data.get("facts", {}).get("us-gaap", {})

    if not results:
        return [{
            "severity": "WARNING",
            "code": "NO_DATA",
            "year": None,
            "message": "No financial history available"
        }]

    ordered = sorted(
        results,
        key=lambda row: row["period_end"]
    )

    # ===== 1. Detect missing years =====

    years = sorted({int(row["year"]) for row in ordered})

    for previous, current in zip(years, years[1:]):
        for missing_year in range(previous + 1, current):
            issues.append({
                "severity": "WARNING",
                "code": "MISSING_YEAR",
                "year": missing_year,
                "message": f"No selected annual data for {missing_year}"
            })

    # ===== 2. Load all candidate revenue tags =====

    annual_by_tag = {
        tag: get_annual_records(gaap, tag)
        for tag in REVENUE_TAGS
    }

    previous_tag = None

    for row in ordered:
        year = int(row["year"])
        period = (row["period_start"], row["period_end"])
        revenue_tag = row["revenue_tag"]

        # ===== 3. Detect revenue tag changes =====

        if previous_tag is not None and revenue_tag != previous_tag:
            issues.append({
                "severity": "INFO",
                "code": "REVENUE_TAG_SWITCH",
                "year": year,
                "message": (
                    f"Revenue concept changed: "
                    f"{previous_tag} -> {revenue_tag}"
                )
            })

        previous_tag = revenue_tag

        # ===== 4. Detect conflicting revenue concepts =====

        candidates = {
            tag: records[period]["val"]
            for tag, records in annual_by_tag.items()
            if period in records
        }

        if len(set(candidates.values())) > 1:
            issues.append({
                "severity": "WARNING",
                "code": "XBRL_TAG_CONFLICT",
                "year": year,
                "message": (
                    "Different revenue concepts report "
                    f"different values: {candidates}"
                )
            })

        # ===== 5. Detect historical value changes =====

        metrics = [
            ("Revenue", revenue_tag),
            ("Net Income", row["net_income_tag"])
        ]

        for metric, tag in metrics:
            records = (
                gaap.get(tag, {})
                .get("units", {})
                .get("USD", [])
            )

            values_by_filing = {}

            for record in records:
                if (
                    record.get("start") == period[0]
                    and record.get("end") == period[1]
                    and record.get("form") in ("10-K", "10-K/A")
                    and record.get("fp") == "FY"
                    and record.get("accn")
                    and isinstance(record.get("val"), (int, float))
                    and not isinstance(record.get("val"), bool)
                ):
                    values_by_filing[record["accn"]] = record["val"]

            if len(set(values_by_filing.values())) > 1:
                issues.append({
                    "severity": "WARNING",
                    "code": "HISTORICAL_VALUE_CHANGED",
                    "year": year,
                    "message": (
                        f"{metric} has different reported "
                        "values across SEC filings"
                    )
                })

    return issues
