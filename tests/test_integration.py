
import sqlite3
import pytest
import sec_client
import database
import provenance

from analytics import analyze_company
from validator import validate_financial_data


# ===== Create Mock SEC Data =====

def make_fact(year, revenue_or_income):
    return {
        "start": f"{year}-01-01",
        "end": f"{year}-12-31",
        "val": revenue_or_income,
        "form": "10-K",
        "fp": "FY",
        "filed": f"{year + 1}-02-15",
        "accn": f"0000320193-{(year + 1) % 100:02d}-000101"
    }


def test_financial_pipeline(tmp_path, monkeypatch):

    # Use a temporary database, not the real one
    test_db = tmp_path / "test_finscope.db"

    monkeypatch.setattr(database, "DB_PATH", test_db)
    monkeypatch.setattr(provenance, "DB_PATH", test_db)

    company_data = {
        "cik": 320193,
        "entityName": "Test Company",
        "facts": {
            "us-gaap": {
                "Revenues": {
                    "units": {
                        "USD": [
                            make_fact(2023, 100_000_000),
                            make_fact(2024, 120_000_000)
                        ]
                    }
                },
                "NetIncomeLoss": {
                    "units": {
                        "USD": [
                            make_fact(2023, 20_000_000),
                            make_fact(2024, 24_000_000)
                        ]
                    }
                }
            }
        }
    }

    # Mock HTTP requests to SEC
    class MockResponse:
        def __init__(self, data):
            self.data = data

        def raise_for_status(self):
            pass

        def json(self):
            return self.data

    def fake_get(url, headers, timeout):

        if url.endswith("company_tickers.json"):
            return MockResponse({
                "0": {
                    "ticker": "TEST",
                    "cik_str": 320193
                }
            })

        if "companyfacts/CIK0000320193.json" in url:
            return MockResponse(company_data)

        raise AssertionError(f"Unexpected URL: {url}")

    monkeypatch.setattr(
        sec_client.requests,
        "get",
        fake_get
    )

    # ===== 1. Test SEC Client =====

    headers = {"User-Agent": "FinScope Test"}

    cik = sec_client.get_company_cik("TEST", headers)

    assert cik == "0000320193"

    data = sec_client.get_company_facts(cik, headers)

    assert data["entityName"] == "Test Company"

    # ===== 2. Test Financial Analysis =====

    results = analyze_company(data)

    assert len(results) == 2
    assert results[1]["revenue"] == 120_000_000
    assert results[1]["revenue_growth"] == pytest.approx(20.0)

    # ===== 3. Test Validation =====

    warnings = validate_financial_data(results)

    assert warnings == []

    # ===== 4. Test Database Storage =====

    database.save_to_database(
        cik,
        data["entityName"],
        results
    )

    # Repeated writes should not create duplicates
    database.save_to_database(
        cik,
        data["entityName"],
        results
    )

    with sqlite3.connect(test_db) as conn:
        count = conn.execute(
            "SELECT COUNT(*) FROM annual_financials"
        ).fetchone()[0]

    assert count == 2

    # ===== 5. Test SEC Provenance =====

    provenance.save_provenance(cik, results)

    sources = provenance.get_provenance(cik)

    assert len(sources) == 4

    assert any(
        record["metric"] == "Revenue"
        and record["reported_value"] == 120_000_000
        for record in sources
    )
