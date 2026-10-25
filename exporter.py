
import csv
from pathlib import Path


def export_csv(ticker, results):
    filename = (
        Path(__file__).resolve().parent
        / f"{ticker}_history.csv"
    )

    with open(filename, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=results[0].keys()
        )

        writer.writeheader()
        writer.writerows(results)

    print(f"Saved CSV: {filename.name}")
