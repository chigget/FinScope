
from normalizer import (
    get_annual_records,
    normalize_revenue
)
from analytics import analyze_company
from validator import validate_financial_data

# Create sample SEC records
def fact(year, value, filed):
    return {
        "start": f"{year}-01-01",
        "end": f"{year}-12-31",
        "val": value,
        "filed": filed,
        "accn": "0000320193-25-000079",
        "form": "10-K",
        "fp": "FY"
    }


# Test 1: Revenue tags change across years
def test_different_revenue_tags():

    gaap = {
        "RevenueFromContractWithCustomerExcludingAssessedTax": {
            "units": {
                "USD": [fact(2025, 160, "2026-01-15")]
            }
        },
        "Revenues": {
            "units": {
                "USD": [fact(2024, 140, "2025-01-15")]
            }
        }
    }

    result = normalize_revenue(gaap)

    assert len(result) == 2
    assert result[("2024-01-01", "2024-12-31")]["val"] == 140
    assert result[("2025-01-01", "2025-12-31")]["val"] == 160


# Test 2: Prefer the newer filing
def test_latest_filing():

    gaap = {
        "Revenues": {
            "units": {
                "USD": [
                    fact(2024, 100, "2025-01-15"),
                    fact(2024, 105, "2025-10-15")
                ]
            }
        }
    }

    result = get_annual_records(gaap, "Revenues")

    assert result[("2024-01-01", "2024-12-31")]["val"] == 105


# Test 3: Ignore quarterly records
def test_ignore_quarterly():

    quarterly = fact(2024, 55, "2024-05-10")
    quarterly["end"] = "2024-03-31"

    gaap = {
        "Revenues": {
            "units": {
                "USD": [quarterly]
            }
        }
    }

    assert get_annual_records(gaap, "Revenues") == {}


# Test 4: Prefer the primary revenue concept
def test_revenue_tag_priority():

    gaap = {
        "RevenueFromContractWithCustomerExcludingAssessedTax": {
            "units": {
                "USD": [fact(2024, 120, "2025-01-15")]
            }
        },
        "Revenues": {
            "units": {
                "USD": [fact(2024, 999, "2025-01-16")]
            }
        }
    }

    result = normalize_revenue(gaap)

    record = result[("2024-01-01", "2024-12-31")]

    assert record["val"] == 120


# Test 5: Full analysis preserves source tags
def test_analysis_with_different_tags():

    gaap = {
        "RevenueFromContractWithCustomerExcludingAssessedTax": {
            "units": {
                "USD": [fact(2024, 120, "2025-01-15")]
            }
        },
        "Revenues": {
            "units": {
                "USD": [fact(2023, 100, "2024-01-15")]
            }
        },
        "NetIncomeLoss": {
            "units": {
                "USD": [
                    fact(2023, 20, "2024-01-15"),
                    fact(2024, 24, "2025-01-15")
                ]
            }
        }
    }

    results = analyze_company({
        "facts": {
            "us-gaap": gaap
        }
    })

    assert len(results) == 2
    assert results[0]["revenue_tag"] == "Revenues"
    assert abs(results[1]["revenue_growth"] - 20) < 0.001


# Test 6: Missing year must not produce YoY growth

def test_missing_year_does_not_create_yoy():

    gaap = {
        "Revenues": {
            "units": {
                "USD": [
                    fact(2022, 100, "2023-01-15"),
                    fact(2024, 130, "2025-01-15")
                ]
            }
        },
        "NetIncomeLoss": {
            "units": {
                "USD": [
                    fact(2022, 20, "2023-01-15"),
                    fact(2024, 26, "2025-01-15")
                ]
            }
        }
    }

    results = analyze_company({
        "facts": {
            "us-gaap": gaap
        }
    })

    assert len(results) == 2

    # 30% across two years is NOT YoY growth
    assert results[1]["revenue_growth"] is None

    warnings = validate_financial_data(results)

    assert any(
        "Unusual reporting gap" in warning
        for warning in warnings
    )
