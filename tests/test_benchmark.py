
import pytest

from benchmark import build_peer_benchmark


def sample_histories():
    return {
        "Company A": [
            {
                "period_end": "2024-12-31",
                "revenue": 120_000_000_000,
                "net_income": 30_000_000_000,
                "revenue_growth": 20.0
            }
        ],
        "Company B": [
            {
                "period_end": "2024-06-30",
                "revenue": 200_000_000_000,
                "net_income": 20_000_000_000,
                "revenue_growth": 10.0
            }
        ]
    }


def test_peer_median():
    result = build_peer_benchmark(sample_histories())

    assert result["year"] == 2024
    assert result["median_margin"] == 17.5
    assert result["median_growth"] == 15.0


def test_margin_ranking():
    result = build_peer_benchmark(sample_histories())

    assert result["rows"][0]["Company"] == "Company A"
    assert result["rows"][0]["Margin Rank"] == 1
    assert result["rows"][1]["Margin Rank"] == 2


def test_requires_two_companies():
    data = sample_histories()

    del data["Company B"]

    with pytest.raises(ValueError):
        build_peer_benchmark(data)


def test_no_common_year():
    data = sample_histories()

    data["Company B"][0]["period_end"] = "2025-06-30"

    with pytest.raises(
        ValueError,
        match="no common reporting year"
    ):
        build_peer_benchmark(data)
