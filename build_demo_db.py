
import sqlite3
from pathlib import Path
from contextlib import closing

ROOT = Path(__file__).resolve().parent

SOURCE = ROOT / "finscope.db"
DEST = ROOT / "data" / "finscope_demo.db"

TABLES = [
    "annual_financials",
    "financial_sources",
    "quality_reports"
]


def build_demo_database():
    if not SOURCE.exists():
        raise FileNotFoundError(
            "Run main.py to create finscope.db first."
        )

    DEST.parent.mkdir(exist_ok=True)

    if DEST.exists():
        DEST.unlink()

    with closing(sqlite3.connect(SOURCE)) as source:
        with closing(sqlite3.connect(DEST)) as target:

            for table in TABLES:
                schema = source.execute(
                    """
                    SELECT sql FROM sqlite_master
                    WHERE type = 'table' AND name = ?
                    """,
                    (table,)
                ).fetchone()

                if schema is None:
                    raise ValueError(
                        f"Missing database table: {table}"
                    )

                target.execute(schema[0])

                records = source.execute(
                    f"SELECT * FROM {table}"
                ).fetchall()

                column_count = len(
                    source.execute(
                        f"PRAGMA table_info({table})"
                    ).fetchall()
                )

                placeholders = ",".join(
                    ["?"] * column_count
                )

                target.executemany(
                    f"INSERT INTO {table} VALUES ({placeholders})",
                    records
                )

                print(f"{table}: {len(records)} rows")

            target.commit()

    print(f"\nDemo database created: {DEST}")


if __name__ == "__main__":
    build_demo_database()
