
import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).resolve().parent / "finscope.db"


def save_to_database(cik, company, results):
    connection = sqlite3.connect(DB_PATH)

    try:
        cursor = connection.cursor()

        cursor.execute("""
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

        for row in results:
            cursor.execute("""
            INSERT INTO annual_financials (
                cik, company, fiscal_year, period_end,
                revenue, net_income, profit_margin,
                revenue_growth, revenue_filing, net_income_filing
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(cik, period_end)
            DO UPDATE SET
                company = excluded.company,
                fiscal_year = excluded.fiscal_year,
                revenue = excluded.revenue,
                net_income = excluded.net_income,
                profit_margin = excluded.profit_margin,
                revenue_growth = excluded.revenue_growth,
                revenue_filing = excluded.revenue_filing,
                net_income_filing = excluded.net_income_filing
            """, (
                cik,
                company,
                row["year"],
                row["period_end"],
                row["revenue"],
                row["net_income"],
                row["profit_margin"],
                row["revenue_growth"],
                row["revenue_filing"],
                row["net_income_filing"]
            ))

        connection.commit()

    finally:
        connection.close()
