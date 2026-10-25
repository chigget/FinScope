
import re
import sqlite3
from contextlib import closing

from database import DB_PATH


# ===== SEC Filing URL =====

def build_filing_url(cik, accession):

    if not re.fullmatch(
        r"\d{10}-\d{2}-\d{6}",
        accession
    ):
        raise ValueError(
            f"Invalid accession number: {accession}"
        )

    cik_number = str(int(cik))
    accession_folder = accession.replace("-", "")

    return (
        "https://www.sec.gov/Archives/edgar/data/"
        f"{cik_number}/{accession_folder}/"
        f"{accession}-index.html"
    )


# ===== Save Financial Sources =====

def save_provenance(cik, results):

    with closing(sqlite3.connect(DB_PATH)) as conn:

        conn.execute("""
        CREATE TABLE IF NOT EXISTS financial_sources (
            cik TEXT NOT NULL,
            period_end TEXT NOT NULL,
            metric TEXT NOT NULL,
            period_start TEXT NOT NULL,
            xbrl_tag TEXT NOT NULL,
            accession TEXT NOT NULL,
            filed_date TEXT NOT NULL,
            reported_value INTEGER NOT NULL,
            PRIMARY KEY (cik, period_end, metric)
        )
        """)

        for row in results:

            sources = [
                (
                    "Revenue",
                    row["revenue"],
                    row["revenue_tag"],
                    row["revenue_filed"],
                    row["revenue_filing"]
                ),
                (
                    "Net Income",
                    row["net_income"],
                    row["net_income_tag"],
                    row["net_income_filed"],
                    row["net_income_filing"]
                )
            ]

            for metric, value, tag, filed, accession in sources:

                # Check that the filing ID is valid
                build_filing_url(cik, accession)

                conn.execute("""
                INSERT INTO financial_sources (
                    cik,
                    period_end,
                    metric,
                    period_start,
                    xbrl_tag,
                    accession,
                    filed_date,
                    reported_value
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(cik, period_end, metric)
                DO UPDATE SET
                    period_start = excluded.period_start,
                    xbrl_tag = excluded.xbrl_tag,
                    accession = excluded.accession,
                    filed_date = excluded.filed_date,
                    reported_value = excluded.reported_value
                """, (
                    cik,
                    row["period_end"],
                    metric,
                    row["period_start"],
                    tag,
                    accession,
                    filed,
                    value
                ))

        conn.commit()


# ===== Retrieve Financial Sources =====

def get_provenance(cik):

    with closing(sqlite3.connect(DB_PATH)) as conn:

        conn.row_factory = sqlite3.Row

        records = conn.execute("""
        SELECT
            period_end,
            metric,
            period_start,
            xbrl_tag,
            accession,
            filed_date,
            reported_value
        FROM financial_sources
        WHERE cik = ?
        ORDER BY period_end DESC, metric
        """, (cik,)).fetchall()

        return [dict(record) for record in records]
