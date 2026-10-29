
import pytest

from insights import generate_insights


def sample_rows():
    return [
        {
            "period_end": "2023-09-30",
            "revenue": 100_000_000_000,
            "net_income": 20_000_000_000
        },
        {
            "period_end": "2024-09-28",
            "revenue": 110_000_000_000,
            "net_income": 22_000_000_000
        },
        {
            "period_end": "2025-09-27",
            "revenue": 121_000_000_000,
            "net_income": 26_620_000_000
        }
    ]


def test_latest_revenue_growth():
    insights = generate_insights(sample_rows())

    assert any(
        x["title"] == "Revenue growth: +10.00%"
        for x in insights
    )


def test_profit_margin_change():
    insights = generate_insights(sample_rows())

    assert any(
        x["title"] == (
            "Net margin change: +2.00 percentage points"
        )
        for x in insights
    )


def test_cagr():
    insights = generate_insights(sample_rows())

    assert any(
        "Revenue CAGR" in x["title"]
        for x in insights
    )


def test_missing_year():
    rows = [
        sample_rows()[0],
        sample_rows()[2]
    ]

    insights = generate_insights(rows)

    assert any(
        x["level"] == "warning"
        for x in insights
    )

    assert not any(
        x["title"].startswith("Revenue growth:")
        for x in insights
    )


def test_invalid_revenue():
    rows = sample_rows()
    rows[-1]["revenue"] = 0

    with pytest.raises(
        ValueError,
        match="revenue must be positive"
    ):
        generate_insights(rows)
