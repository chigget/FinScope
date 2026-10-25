
import requests


def fetch_json(url, headers):
    response = requests.get(
        url,
        headers=headers,
        timeout=25
    )

    response.raise_for_status()
    return response.json()


def get_company_cik(ticker, headers):
    url = "https://www.sec.gov/files/company_tickers.json"

    companies = fetch_json(url, headers)

    for company in companies.values():
        if company["ticker"].upper() == ticker.upper():
            return str(company["cik_str"]).zfill(10)

    raise ValueError(f"Ticker not found: {ticker}")


def get_company_facts(cik, headers):
    url = (
        "https://data.sec.gov/api/xbrl/companyfacts/"
        f"CIK{cik}.json"
    )

    return fetch_json(url, headers)
