import sqlite3
import requests
import csv
from datetime import date

# SEC API Configuration
CIK = "0000320193"

url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{CIK}.json"

headers = {
    "User-Agent": "FinScope your_email@example.com"
}

# Fetch financial data
response = requests.get(url, headers=headers, timeout=20)
response.raise_for_status()

data = response.json()

if "facts" not in data or "us-gaap" not in data["facts"]:
    raise ValueError("Missing financial data")

financial_data = data["facts"]["us-gaap"]


# Get annual financial records
def get_annual_records(metric):
    records = financial_data[metric]["units"]["USD"]

    annual_data = {}

    for record in records:

        if record.get("form") != "10-K":
            continue

        if record.get("fp") != "FY":
            continue

        if not all(k in record for k in ("start", "end", "filed", "val")):
            continue

        start = date.fromisoformat(record["start"])
        end = date.fromisoformat(record["end"])

        duration = (end - start).days

        if not 330 <= duration <= 390:
            continue

        # Use exact reporting period as the key
        period = (record["start"], record["end"])

        # Keep the latest filed version of each period
        old = annual_data.get(period)

        if old is None or record["filed"] > old["filed"]:
            annual_data[period] = record

    return annual_data


# Extract revenue and net income
revenue_data = get_annual_records(
    "RevenueFromContractWithCustomerExcludingAssessedTax"
)

net_income_data = get_annual_records("NetIncomeLoss")

# Match reporting periods
common_periods = set(revenue_data) & set(net_income_data)

# Get the most recent six years
# Six years allows five YoY growth calculations
periods = sorted(
    common_periods,
    key=lambda period: period[1]
)[-6:]

if len(periods) < 2:
    raise ValueError("Not enough annual financial data")

history = []

for start, end in periods:

    revenue = revenue_data[(start, end)]["val"]
    net_income = net_income_data[(start, end)]["val"]

    if revenue <= 0:
        raise ValueError(f"Invalid revenue for {end}")

    profit_margin = net_income / revenue * 100

    # Calculate year-over-year revenue growth
    growth = None

    if history:
        previous_revenue = history[-1]["revenue"]

        if previous_revenue > 0:
            growth = (
                (revenue - previous_revenue)
                / previous_revenue
                * 100
            )

    history.append({
        "year": end[:4],
        "period_end": end,
        "revenue": revenue,
        "net_income": net_income,
        "profit_margin": profit_margin,
        "revenue_growth": growth,
        "revenue_filing": revenue_data[(start, end)]["accn"],
        "net_income_filing": net_income_data[(start, end)]["accn"]
    })


# Display the most recent five years
results = history[-5:]

print("\n===== FinScope Financial Analysis =====")
print("Company:", data["entityName"])
print("Source: SEC EDGAR")
print("Reporting periods matched: PASSED\n")

for row in results:

    print("Fiscal Year:", row["year"])
    print(f"Revenue: ${row['revenue'] / 1e9:.2f}B")
    print(f"Net Income: ${row['net_income'] / 1e9:.2f}B")
    print(f"Profit Margin: {row['profit_margin']:.2f}%")

    if row["revenue_growth"] is not None:
        print(f"Revenue Growth: {row['revenue_growth']:.2f}%")
    else:
        print("Revenue Growth: N/A")

    print("------------------------------")


# Save financial history to CSV
with open("apple_history.csv", "w", newline="", encoding="utf-8") as file:

    writer = csv.DictWriter(file, fieldnames=results[0].keys())

    writer.writeheader()
    writer.writerows(results)

print("\nFinancial history saved to apple_history.csv")


# SQLite Database

connection = sqlite3.connect("finscope.db")
cursor = connection.cursor()

# Create financial data table
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

# Insert financial data
for row in results:
    cursor.execute("""
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
        CIK,
        data["entityName"],
        int(row["year"]),
        row["period_end"],
        row["revenue"],
        row["net_income"],
        row["profit_margin"],
        row["revenue_growth"],
        row["revenue_filing"],
        row["net_income_filing"]
    ))

connection.commit()

# Query data from database
cursor.execute("""
SELECT fiscal_year, revenue, net_income
FROM annual_financials
WHERE cik = ?
ORDER BY fiscal_year
""", (CIK,))

records = cursor.fetchall()

print("\n===== FinScope Database =====")

for year, revenue, net_income in records:
    print(
        f"{year} | Revenue: ${revenue / 1e9:.2f}B"
        f" | Net Income: ${net_income / 1e9:.2f}B"
    )

connection.close()

print("\nDatabase updated successfully!")
