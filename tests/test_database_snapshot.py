
import sqlite3

import database
import provenance


def make_row(year):
    return {
        "year": year,
        "period_start": f"{year}-01-01",
        "period_end": f"{year}-12-31",
        "revenue": 100_000_000,
        "net_income": 20_000_000,
        "profit_margin": 20.0,
        "revenue_growth": None,
        "revenue_filing": "0000320193-25-000101",
        "net_income_filing": "0000320193-25-000101",
        "revenue_tag": "Revenues",
        "revenue_filed": "2025-02-15",
        "net_income_tag": "NetIncomeLoss",
        "net_income_filed": "2025-02-15"
    }


def test_snapshot_replaces_old_years(tmp_path, monkeypatch):

    test_db = tmp_path / "snapshot.db"

    monkeypatch.setattr(database, "DB_PATH", test_db)
    monkeypatch.setattr(provenance, "DB_PATH", test_db)

    cik = "0000320193"
    company = "Test Company"

    # Initial history: 2022 and 2023
    first = [make_row(2022), make_row(2023)]

    database.save_to_database(cik, company, first)
    provenance.save_provenance(cik, first)

    # Updated history: 2023 and 2024
    second = [make_row(2023), make_row(2024)]

    database.save_to_database(cik, company, second)
    provenance.save_provenance(cik, second)

    with sqlite3.connect(test_db) as conn:

        years = [
            row[0]
            for row in conn.execute(
                """
                SELECT fiscal_year
                FROM annual_financials
                ORDER BY fiscal_year
                """
            )
        ]

    assert years == [2023, 2024]

    sources = provenance.get_provenance(cik)

    assert len(sources) == 4

    assert {
        source["period_end"] for source in sources
    } == {"2023-12-31", "2024-12-31"}
