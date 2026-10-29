
import requests
import sqlite3

from sec_client import get_company_cik, get_company_facts
from analytics import analyze_company
from database import save_to_database
from exporter import export_csv
from validator import validate_financial_data
from provenance import save_provenance
from quality import analyze_data_quality
from quality_store import save_quality_report

def main():
    print("===== Welcome to FinScope =====")

    ticker = input("Enter stock ticker: ").strip().upper()
    email = input("SEC contact email: ").strip()

    if not ticker or not email:
        raise ValueError("Ticker and email are required")

    headers = {
        "User-Agent": f"FinScope {email}"
    }

    # Step 1: Fetch financial data
    print("\nFetching financial data...")

    cik = get_company_cik(ticker, headers)
    data = get_company_facts(cik, headers)

    if "facts" not in data or "us-gaap" not in data["facts"]:
        raise ValueError("Missing US-GAAP financial data")

    company = data["entityName"]

    # Step 2: Analyze company
    print("Analyzing financial statements...")

    results = analyze_company(data)

    quality_issues = analyze_data_quality(data, results)

    print("\n===== Financial Data Quality Report =====")

    if not quality_issues:
        print("No issues detected by current quality rules.")

    else:
        for issue in quality_issues:
            print(
                f"[{issue['severity']}] "
                f"{issue['code']} "
                f"(FY{issue['year']}): "
                f"{issue['message']}"
            )

        print(f"\nTotal findings: {len(quality_issues)}")


    # Step 3: Validate financial data
    print("Validating financial data...")

    warnings = validate_financial_data(results)

    print("\n===== Validation Report =====")
    print("Core Validation: PASSED")
    print("Warnings:", len(warnings))

    for warning in warnings:
        print("-", warning)

    # Step 4: Display financial results
    print(f"\n===== {company} Financial Report =====")

    for row in results:
        print(f"\nFiscal Year: {row['year']}")
        print(f"Revenue: ${row['revenue'] / 1e9:.2f}B")
        print(f"Net Income: ${row['net_income'] / 1e9:.2f}B")
        print(f"Profit Margin: {row['profit_margin']:.2f}%")

        if row["revenue_growth"] is not None:
            print(
                f"Revenue Growth: "
                f"{row['revenue_growth']:.2f}%"
            )

    # Step 5: Save data
    save_to_database(cik, company, results)
    save_provenance(cik, results)
    save_quality_report(cik, quality_issues)

    # Step 6: Export CSV
    export_csv(ticker, results)

    print("\nFinScope completed successfully!")


if __name__ == "__main__":
    try:
        main()
    except (
        requests.RequestException,
        ValueError,
        KeyError,
        sqlite3.Error,
        OSError
    ) as error:
        print("Error:", error)
