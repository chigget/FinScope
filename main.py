
import requests
import sqlite3
import csv
from datetime import date


# ===== SEC API =====

def fetch_json(url, headers):
    response = requests.get(
        url,
        headers=headers,
        timeout=25
    )

    response.raise_for_status()
    return response.json()


# ===== Find Company CIK =====

def get_company_cik(ticker, headers):
    url = "https://www.sec.gov/files/company_tickers.json"

    companies = fetch_json(url, headers)

    for company in companies.values():
        if company["ticker"].upper() == ticker:
            return str(company["cik_str"]).zfill(10)

    raise ValueError(f"Ticker not found: {ticker}")


# ===== Extract Annual Financial Data =====

def get_annual_records(financial_data, metric):
    if metric not in financial_data:
        return {}

    records = financial_data[metric]["units"].get("USD", [])

    annual_data = {}

    for record in records:
        if record.get("form") != "10-K":
            continue

        if record.get("fp") != "FY":
            continue

        required = ("start", "end", "filed", "val")

        if not all(key in record for key in required):
            continue

        start = date.fromisoformat(record["start"])
        end = date.fromisoformat(record["end"])

        duration = (end - start).days

        if not 330 <= duration <= 390:
            continue

        period = (record["start"], record["end"])

        previous = annual_data.get(period)

        if previous is None or record["filed"] > previous["filed"]:
            annual_data[period] = record

    return annual_data


# ===== Calculate Financial Metrics =====

def analyze_company(data):
    financial_data = data["facts"]["us-gaap"]

    # Try common revenue XBRL tags
    revenue_tags = [
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "Revenues",
        "SalesRevenueNet"
    ]

    revenue_data = {}

    for tag in revenue_tags:
        revenue_data = get_annual_records(
            financial_data, tag
        )

        if revenue_data:
            print("Revenue XBRL Tag:", tag)
            break

    net_income_data = get_annual_records(
        financial_data, "NetIncomeLoss"
    )

    common_periods = set(revenue_data) & set(net_income_data)

    periods = sorted(
        common_periods,
        key=lambda period: period[1]
    )[-6:]

    if len(periods) < 2:
        raise ValueError("Not enough comparable annual data")

    history = []

    for start, end in periods:
        revenue_record = revenue_data[(start, end)]
        income_record = net_income_data[(start, end)]

        revenue = revenue_record["val"]
        net_income = income_record["val"]

        if revenue <= 0:
            raise ValueError(f"Invalid revenue: {end}")

        profit_margin = net_income / revenue * 100

        growth = None

        if history:
            previous_revenue = history[-1]["revenue"]

            if previous_revenue > 0:
                growth = (
                    (revenue - previous_revenue)
                    / previous_revenue * 100
                )

        history.append({
            "year": int(end[:4]),
            "period_end": end,
            "revenue": revenue,
            "net_income": net_income,
            "profit_margin": profit_margin,
            "revenue_growth": growth,
            "revenue_filing": revenue_record.get("accn"),
            "net_income_filing": income_record.get("accn")
        })

    return history[-5:]


# ===== SQLite Database =====

def save_to_database(cik, company, results):
    connection = sqlite3.connect("finscope.db")
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
        INSERT INTO annual_financials
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
    connection.close()


# ===== CSV Export =====

def export_csv(ticker, results):
    filename = f"{ticker}_history.csv"

    with open(filename, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=results[0].keys()
        )

        writer.writeheader()
        writer.writerows(results)

    print(f"\nSaved CSV: {filename}")


# ===== Main Program =====

def main():
    print("===== Welcome to FinScope =====")

    ticker = input("Enter stock ticker: ").strip().upper()

    email = input("SEC contact email: ").strip()

    if not ticker or not email:
        print("Ticker and contact email are required.")
        return

    headers = {
        "User-Agent": f"FinScope {email}"
    }

    cik = get_company_cik(ticker, headers)

    url = (
        "https://data.sec.gov/api/xbrl/companyfacts/"
        f"CIK{cik}.json"
    )

    data = fetch_json(url, headers)

    if "facts" not in data or "us-gaap" not in data["facts"]:
        raise ValueError("Missing US-GAAP financial data")

    company = data["entityName"]
    results = analyze_company(data)

    print(f"\n===== {company} Financial Report =====")

    for row in results:
        print(f"\nFiscal Year: {row['year']}")
        print(f"Revenue: ${row['revenue'] / 1e9:.2f}B")
        print(f"Net Income: ${row['net_income'] / 1e9:.2f}B")
        print(f"Profit Margin: {row['profit_margin']:.2f}%")

        if row["revenue_growth"] is not None:
            print(f"Revenue Growth: {row['revenue_growth']:.2f}%")

    save_to_database(cik, company, results)
    export_csv(ticker, results)

    print("\nDatabase updated successfully!")


if __name__ == "__main__":
    try:
        main()
    except (requests.RequestException, ValueError, KeyError) as error:
        print("Error:", error)

