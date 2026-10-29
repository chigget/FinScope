
import sqlite3
from pathlib import Path
from contextlib import closing


DB_PATH = Path(__file__).resolve().parent / "finscope.db"


def save_to_database(cik, company, results):

    if not results:
        raise ValueError("No financial records to save")

    with closing(sqlite3.connect(DB_PATH)) as conn:

        # All changes are part of one transaction
        with conn:

            conn.execute("""
                CREATE TABLE IF NOT EXISTS annual_financials (
                    cik TEXT NOT NULL,
                    company TEXT NOT NULL,
                    fiscal_year INTEGER NOT NULL,
                    period_end TEXT NOT NULL,
                    revenue INTEGER NOT NULL,
                    net_income INTEGER NOT NULL,
                    profit_margin REAL NOT NULL,
                    revenue_growth REAL,
                    revenue_filing TEXT,
                    net_income_filing TEXT,
                    PRIMARY KEY (cik, period_end)
                )
            """)

            # Remove only this company's old records
            conn.execute(
                "DELETE FROM annual_financials WHERE cik = ?",
                (str(cik),)
            )

            # Insert the new validated financial history
            rows = [
                (
                    str(cik),
                    company,
                    row["year"],
                    row["period_end"],
                    row["revenue"],
                    row["net_income"],
                    row["profit_margin"],
                    row["revenue_growth"],
                    row["revenue_filing"],
                    row["net_income_filing"]
                )
                for row in results
            ]

            conn.executemany("""
                INSERT INTO annual_financials (
                    cik,
                    company,
                    fiscal_year,
                    period_end,
                    revenue,
                    net_income,
                    profit_margin,
                    revenue_growth,
                    revenue_filing,
                    net_income_filing
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, rows)
