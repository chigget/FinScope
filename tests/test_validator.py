
import pytest

from validator import validate_financial_data


# ===== Test Data =====

@pytest.fixture
def sample_data():
    return [
        {
            "year": 2023,
            "period_end": "2023-09-30",
            "revenue": 100_000_000,
            "net_income": 20_000_000,
            "profit_margin": 20.0,
            "revenue_growth": None,
            "revenue_filing": "0000320193-23-000111",
            "net_income_filing": "0000320193-23-000111"
        },
        {
            "year": 2024,
            "period_end": "2024-09-28",
            "revenue": 110_000_000,
            "net_income": 22_000_000,
            "profit_margin": 20.0,
            "revenue_growth": 10.0,
            "revenue_filing": "0000320193-24-000222",
            "net_income_filing": "0000320193-24-000222"
        }
    ]


# ===== Test 1: Valid Financial Data =====

def test_valid_financial_data(sample_data):
    warnings = validate_financial_data(sample_data)

    assert warnings == []


# ===== Test 2: Incorrect Profit Margin =====

def test_invalid_profit_margin(sample_data):
    sample_data[1]["profit_margin"] = 25.0

    with pytest.raises(
        ValueError,
        match="Incorrect profit margin"
    ):
        validate_financial_data(sample_data)


# ===== Test 3: Incorrect Revenue Growth =====

def test_invalid_revenue_growth(sample_data):
    sample_data[1]["revenue_growth"] = 15.0

    with pytest.raises(
        ValueError,
        match="Incorrect revenue growth"
    ):
        validate_financial_data(sample_data)


# ===== Test 4: Duplicate Reporting Period =====

def test_duplicate_period(sample_data):
    sample_data.append(sample_data[1].copy())

    with pytest.raises(
        ValueError,
        match="Duplicate period"
    ):
        validate_financial_data(sample_data)


# ===== Test 5: Missing Required Field =====

def test_missing_revenue(sample_data):
    del sample_data[0]["revenue"]

    with pytest.raises(
        ValueError,
        match="Missing required field"
    ):
        validate_financial_data(sample_data)


# ===== Test 6: Invalid Reporting Date =====

def test_invalid_date(sample_data):
    sample_data[1]["period_end"] = "2024-99-99"

    with pytest.raises(
        ValueError,
        match="Invalid reporting date"
    ):
        validate_financial_data(sample_data)


# ===== Test 7: Different SEC Filings =====

def test_different_filing_warning(sample_data):
    sample_data[1]["net_income_filing"] = (
        "0000320193-24-000333"
    )

    warnings = validate_financial_data(sample_data)

    assert len(warnings) == 1
    assert "different filings" in warnings[0]


# Test 8: Reject YoY growth across missing years

def test_invalid_growth_across_gap(sample_data):

    sample_data[1]["year"] = 2025
    sample_data[1]["period_end"] = "2025-09-27"

    with pytest.raises(
        ValueError,
        match="reporting gap"
    ):
        validate_financial_data(sample_data)
