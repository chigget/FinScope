
import json
import sqlite3

from datetime import datetime, timezone
from contextlib import closing
from database import DB_PATH


# ===== Save Quality Report =====

def save_quality_report(cik, issues):

    checked_at = datetime.now(
        timezone.utc
    ).isoformat(timespec="seconds")

    with closing(sqlite3.connect(DB_PATH)) as conn:

        with conn:
            conn.execute("""
            CREATE TABLE IF NOT EXISTS quality_reports (
                cik TEXT PRIMARY KEY,
                checked_at TEXT NOT NULL,
                issues_json TEXT NOT NULL
            )
            """)

            conn.execute("""
            INSERT INTO quality_reports (
                cik, checked_at, issues_json
            )
            VALUES (?, ?, ?)
            ON CONFLICT(cik)
            DO UPDATE SET
                checked_at = excluded.checked_at,
                issues_json = excluded.issues_json
            """, (
                cik,
                checked_at,
                json.dumps(issues)
            ))


# ===== Load Quality Report =====

def get_quality_report(cik):

    if not DB_PATH.exists():
        return None

    with closing(sqlite3.connect(DB_PATH)) as conn:

        # Check whether the report table exists
        table = conn.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
          AND name = 'quality_reports'
        """).fetchone()

        if table is None:
            return None

        record = conn.execute("""
        SELECT checked_at, issues_json
        FROM quality_reports
        WHERE cik = ?
        """, (cik,)).fetchone()

    if record is None:
        return None

    return {
        "checked_at": record[0],
        "issues": json.loads(record[1])
    }
