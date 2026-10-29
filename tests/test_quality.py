
from quality import analyze_data_quality


PRIMARY = (
    "RevenueFromContractWithCustomerExcludingAssessedTax"
)


def fact(year, value, accn="0000000000-24-000001"):
    return {
        "start": f"{year}-01-01",
        "end": f"{year}-12-31",
        "form": "10-K",
        "fp": "FY",
        "val": value,
        "filed": f"{year + 1}-02-01",
        "accn": accn
    }


def row(year, tag=PRIMARY):
    return {
        "year": year,
        "period_start": f"{year}-01-01",
        "period_end": f"{year}-12-31",
        "revenue_tag": tag,
        "net_income_tag": "NetIncomeLoss"
    }


def company(revenue, income):
    return {
        "facts": {
            "us-gaap": {
                PRIMARY: {"units": {"USD": revenue}},
                "NetIncomeLoss": {"units": {"USD": income}}
            }
        }
    }


def codes(report):
    return {item["code"] for item in report}


def test_clean_history():
    facts = company(
        [fact(2023, 100), fact(2024, 120)],
        [fact(2023, 20), fact(2024, 24)]
    )

    result = analyze_data_quality(
        facts, [row(2023), row(2024)]
    )

    assert result == []


def test_missing_year():
    facts = company([], [])

    report = analyze_data_quality(
        facts, [row(2022), row(2024)]
    )

    assert "MISSING_YEAR" in codes(report)
    assert any(r["year"] == 2023 for r in report)


def test_conflicting_tags():
    facts = company(
        [fact(2024, 110)],
        [fact(2024, 20)]
    )

    facts["facts"]["us-gaap"]["Revenues"] = {
        "units": {"USD": [fact(2024, 115)]}
    }

    report = analyze_data_quality(facts, [row(2024)])

    assert "XBRL_TAG_CONFLICT" in codes(report)


def test_changed_filing_value():
    revenue = [
        fact(2024, 100, "0000000000-24-000001"),
        fact(2024, 110, "0000000000-25-000002")
    ]

    facts = company(revenue, [fact(2024, 25)])

    report = analyze_data_quality(facts, [row(2024)])

    assert "HISTORICAL_VALUE_CHANGED" in codes(report)


def test_revenue_tag_switch():
    facts = company([], [])

    report = analyze_data_quality(
        facts,
        [row(2023, "Revenues"), row(2024)]
    )

    assert "REVENUE_TAG_SWITCH" in codes(report)
