
import re
import sqlite3
from contextlib import closing

from database import DB_PATH


# ===== Build SEC Filing URL =====

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

    if not results:
        raise ValueError("No provenance records to save")

    with closing(sqlite3.connect(DB_PATH)) as conn:

        with conn:

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

            # Remove previous records for this company
            conn.execute(
                "DELETE FROM financial_sources WHERE cik = ?",
                (str(cik),)
            )

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

                    # Validate the SEC filing reference
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
                    """, (
                        str(cik),
                        row["period_end"],
                        metric,
                        row["period_start"],
                        tag,
                        accession,
                        filed,
                        value
                    ))


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
        """, (str(cik),)).fetchall()

        return [
            dict(record)
            for record in records
        ]
