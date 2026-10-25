import requests
from datetime import date

# SEC API
CIK = "0000320193"
url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{CIK}.json"

headers = {
    "User-Agent": "FinScope wang20070620@gmail.com"
}

# Fetch data
response = requests.get(url, headers=headers, timeout=20)
response.raise_for_status()

data = response.json()

# Basic validation
if "facts" not in data or "us-gaap" not in data["facts"]:
    raise ValueError("Missing financial data")

financial_data = data["facts"]["us-gaap"]


# Extract the latest annual financial record
def get_annual_metric(metric):
    records = financial_data[metric]["units"]["USD"]

    annual_records = []

    for record in records:
        if record.get("form") != "10-K":
            continue

        if record.get("fp") != "FY":
            continue

        if "start" not in record or "end" not in record:
            continue

        start = date.fromisoformat(record["start"])
        end = date.fromisoformat(record["end"])

        duration = (end - start).days

        # Only accept full-year reporting periods
        if 330 <= duration <= 390:
            annual_records.append(record)

    if not annual_records:
        raise ValueError(f"No annual data found for {metric}")

    return max(
        annual_records,
        key=lambda x: (x["end"], x["filed"])
    )


# Get financial metrics
revenue_record = get_annual_metric(
    "RevenueFromContractWithCustomerExcludingAssessedTax"
)

net_income_record = get_annual_metric("NetIncomeLoss")

# Validate reporting periods
if (
    revenue_record["start"] != net_income_record["start"]
    or revenue_record["end"] != net_income_record["end"]
):
    raise ValueError("Financial reporting periods do not match")

revenue = revenue_record["val"]
net_income = net_income_record["val"]

# Calculate net profit margin
if revenue == 0:
    raise ValueError("Revenue cannot be zero")

profit_margin = net_income / revenue * 100

# Display results
print("\n===== FinScope Financial Report =====")
print("Company:", data["entityName"])
print("Period End:", revenue_record["end"])

print(f"Revenue: ${revenue / 1_000_000_000:.2f}B")
print(f"Net Income: ${net_income / 1_000_000_000:.2f}B")
print(f"Net Profit Margin: {profit_margin:.2f}%")

print("\nData Source: SEC EDGAR")
print("Filing Date:", revenue_record["filed"])
print("Accession Number:", revenue_record["accn"])
print("Validation: PASSED")
