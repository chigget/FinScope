# FinScope

**A Financial Intelligence & Analytics Platform built with Python, Streamlit, and SEC EDGAR data.**

[Live Demo](https://finscope-rbvmfk3wzrkra37r42yxiq.streamlit.app/) | [Source Code](https://github.com/chigget/FinScope)

## Overview

FinScope is a Python-based financial analytics application that transforms publicly available SEC financial filings into structured financial metrics, interactive visualizations, and automated insights.

The project focuses on making financial data easier to analyze while improving transparency through source tracking, data validation, and automated quality checks.

## Key Features

- **Financial Data Pipeline:** Retrieve company financial information from SEC EDGAR using ticker-to-CIK lookup and XBRL Company Facts.
- **Historical Financial Analysis:** Calculate annual revenue, net income, net profit margin, revenue growth, and CAGR.
- **Interactive Dashboard:** Explore historical trends and financial metrics through a Streamlit interface.
- **Multi-Company Comparison:** Compare companies' financial performance and historical growth.
- **Peer Benchmarking:** Calculate peer medians and relative performance rankings.
- **Data Validation:** Detect calculation inconsistencies, missing periods, and invalid financial records.
- **SEC Data Provenance:** Trace financial values to their source XBRL concepts and SEC filings.
- **Automated Financial Insights:** Generate deterministic, rule-based financial summaries.
- **Automated Testing:** Run Python tests locally using pytest and automatically through GitHub Actions.

## Technology Stack

| Category | Technologies |
|---|---|
| Programming | Python |
| Data Processing | Pandas, SEC XBRL |
| Database | SQLite |
| Visualization | Streamlit |
| HTTP | Requests |
| Testing | pytest |
| CI | GitHub Actions |
| Deployment | Streamlit Community Cloud |

## Architecture

```text
SEC EDGAR API
      |
      v
SEC Client
      |
      v
XBRL Normalization
      |
      v
Financial Analytics
      |
      +----> Data Validation
      |
      +----> Quality Analysis
      |
      v
SQLite Database
      |
      +----> Financial Insights
      |
      +----> Peer Benchmarking
      |
      v
Streamlit Dashboard
```

## Running Locally

Clone the repository:

```bash
git clone https://github.com/chigget/FinScope.git
cd FinScope
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Launch the dashboard:

```bash
python -m streamlit run app.py
```

To fetch fresh financial data, run:

```bash
python main.py
```

Provide a company ticker and an identifiable contact email for SEC API requests.

## Testing

Run the automated test suite:

```bash
python -m pip install pytest
python -m pytest -v
```

GitHub Actions is configured to execute tests on pushes and pull requests targeting the main branch.

## Data Sources and Limitations

Financial information is obtained from SEC EDGAR and includes publicly reported US-GAAP XBRL data.

The public demo uses a stored database snapshot rather than a continuously updated live feed.

Financial periods may differ across companies. XBRL concepts may also vary by company and reporting year. Quality checks identify selected inconsistencies but do not constitute an audit or establish the reasons behind financial changes.

FinScope is an educational financial analytics project and does not provide investment advice.

## Future Improvements

- More robust fiscal-period alignment
- Improved handling of XBRL concept differences and filing revisions
- Expanded automated and integration testing
- Automated data refresh
- More advanced financial peer analytics

---

**Built as an independent software engineering and financial analytics project.**
