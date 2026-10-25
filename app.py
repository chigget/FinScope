
import streamlit as st
import pandas as pd
import sqlite3

from pathlib import Path
from contextlib import closing
from provenance import get_provenance, build_filing_url

# ===== App Configuration =====

st.set_page_config(
    page_title="FinScope",
    page_icon="📈",
    layout="wide"
)

DB_PATH = Path(__file__).resolve().parent / "finscope.db"


# ===== Database Functions =====

def get_companies():
    with closing(sqlite3.connect(DB_PATH)) as conn:
        companies = pd.read_sql_query(
            """
            SELECT DISTINCT cik, company
            FROM annual_financials
            ORDER BY company
            """,
            conn
        )

    return companies


def get_financial_data(cik):
    with closing(sqlite3.connect(DB_PATH)) as conn:
        df = pd.read_sql_query(
            """
            SELECT
                fiscal_year,
                period_end,
                revenue,
                net_income,
                profit_margin,
                revenue_growth
            FROM annual_financials
            WHERE cik = ?
            ORDER BY period_end
            """,
            conn,
            params=(cik,)
        )

    return df


# ===== Page Header =====

st.title("📈 FinScope")

st.write(
    "Financial Intelligence & Analytics Platform"
)

st.caption("Data Source: SEC EDGAR")


# ===== Check Database =====

if not DB_PATH.exists():
    st.error("Database not found. Run main.py first.")
    st.stop()

try:
    companies = get_companies()
except sqlite3.Error as error:
    st.error(f"Database error: {error}")
    st.stop()

if companies.empty:
    st.warning("No financial data available.")
    st.stop()


# ===== Company Selector =====

company_options = {
    f"{row['company']} ({row['cik']})": row["cik"]
    for _, row in companies.iterrows()
}

selected_company = st.selectbox(
    "Select Company",
    options=list(company_options.keys())
)

selected_cik = company_options[selected_company]

df = get_financial_data(selected_cik)

if df.empty:
    st.warning("No data found for this company.")
    st.stop()


# Financial Metrics 

latest = df.iloc[-1]

revenue = latest["revenue"] / 1e9
net_income = latest["net_income"] / 1e9
profit_margin = latest["profit_margin"]
growth = latest["revenue_growth"]

st.subheader(
    f"Financial Overview — FY{latest['fiscal_year']}"
)

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Revenue",
        f"${revenue:.2f}B",
        delta=(
            f"{growth:.2f}% YoY"
            if pd.notna(growth)
            else None
        )
    )

with col2:
    st.metric(
        "Net Income",
        f"${net_income:.2f}B"
    )

with col3:
    st.metric(
        "Net Profit Margin",
        f"{profit_margin:.2f}%"
    )


# Historical Charts 

st.subheader("Historical Financial Performance")

df["Revenue ($B)"] = df["revenue"] / 1e9
df["Net Income ($B)"] = df["net_income"] / 1e9

st.line_chart(
    df,
    x="fiscal_year",
    y=["Revenue ($B)", "Net Income ($B)"]
)


#  Revenue Growth Chart

st.subheader("Revenue Growth (%)")

st.bar_chart(
    df,
    x="fiscal_year",
    y="revenue_growth"
)


# ===== Financial Data Table =====

st.subheader("Financial Data")

display_df = df[
    [
        "fiscal_year",
        "period_end",
        "Revenue ($B)",
        "Net Income ($B)",
        "profit_margin",
        "revenue_growth"
    ]
].copy()

display_df.columns = [
    "Fiscal Year",
    "Period End",
    "Revenue ($B)",
    "Net Income ($B)",
    "Profit Margin (%)",
    "Revenue Growth (%)"
]

display_df = display_df.round(2)

st.dataframe(
    display_df,
    hide_index=True,
    width="stretch"
)


# ===== CSV Download =====

st.download_button(
    label="Download Financial Data (CSV)",
    data=display_df.to_csv(index=False),
    file_name=f"finscope_{selected_cik}.csv",
    mime="text/csv"
)


# ===== Multi-Company Comparison =====

st.divider()
st.header("Multi-Company Comparison")

# Select two or three companies
selected_companies = st.multiselect(
    "Select companies to compare",
    options=list(company_options.keys()),
    default=list(company_options.keys())[:2],
    max_selections=3
)

if len(selected_companies) < 2:
    st.info("Please select at least two companies.")

else:
    comparison_frames = []
    year_sets = []

    # Load data for every selected company
    for company_label in selected_companies:

        cik = company_options[company_label]
        company_df = get_financial_data(cik)

        if company_df.empty:
            st.warning(f"No data for {company_label}")
            continue

        company_df = company_df.copy()

        # Extract company name
        company_df["Company"] = company_label.rsplit(
            " (", 1
        )[0]

        # Year in which the reporting period ends
        company_df["Year"] = pd.to_datetime(
            company_df["period_end"]
        ).dt.year

        company_df["Revenue ($B)"] = (
            company_df["revenue"] / 1e9
        )

        company_df["Net Income ($B)"] = (
            company_df["net_income"] / 1e9
        )

        company_df["Net Profit Margin (%)"] = (
            company_df["profit_margin"]
        )

        company_df["Revenue Growth (%)"] = (
            company_df["revenue_growth"]
        )

        comparison_frames.append(
            company_df[
                [
                    "Company",
                    "Year",
                    "period_end",
                    "Revenue ($B)",
                    "Net Income ($B)",
                    "Net Profit Margin (%)",
                    "Revenue Growth (%)"
                ]
            ]
        )

        year_sets.append(set(company_df["Year"]))

    if len(comparison_frames) < 2:
        st.warning("Not enough company data.")

    else:
        # Combine company data
        comparison_df = pd.concat(
            comparison_frames,
            ignore_index=True
        )

        st.caption(
            "All amounts are in USD. Companies may "
            "have different fiscal year-end dates. "
            "Year refers to the period-end calendar year."
        )

        # ===== Latest Common Year =====

        common_years = set.intersection(*year_sets)

        if common_years:
            latest_year = max(common_years)

            st.subheader(
                f"Financial Comparison — {latest_year}"
            )

            latest_df = comparison_df[
                comparison_df["Year"] == latest_year
            ].copy()

            st.dataframe(
                latest_df.round(2),
                hide_index=True,
                width="stretch"
            )

        else:
            st.warning("No common reporting year found.")

        # ===== Revenue Comparison =====

        st.subheader("Revenue Comparison ($B)")

        st.line_chart(
            comparison_df,
            x="Year",
            y="Revenue ($B)",
            color="Company"
        )

        # ===== Profit Margin Comparison =====

        st.subheader("Net Profit Margin Comparison (%)")

        st.line_chart(
            comparison_df,
            x="Year",
            y="Net Profit Margin (%)",
            color="Company"
        )

        # ===== Revenue Growth Comparison =====

        st.subheader("Revenue Growth Comparison (%)")

        st.line_chart(
            comparison_df,
            x="Year",
            y="Revenue Growth (%)",
            color="Company"
        )

        # ===== Export =====

        st.download_button(
            "Download Comparison Data",
            data=comparison_df.to_csv(index=False),
            file_name="company_comparison.csv",
            mime="text/csv"
        )


# ===== Lesson 12: SEC Data Provenance =====

st.divider()
st.header("SEC Data Provenance")

st.write(
    "Trace financial metrics to their "
    "original SEC filings."
)

try:
    source_records = get_provenance(selected_cik)

except sqlite3.OperationalError:
    source_records = []

if not source_records:
    st.info(
        "No source records found. "
        "Run main.py for this company first."
    )

else:
    source_df = pd.DataFrame(source_records)

    # Construct filing URLs
    source_df["SEC Filing"] = source_df[
        "accession"
    ].apply(
        lambda accession: build_filing_url(
            selected_cik,
            accession
        )
    )

    # Display financial values in billions
    source_df["Value ($B)"] = (
        source_df["reported_value"] / 1e9
    )

    source_df = source_df.rename(columns={
        "period_end": "Period End",
        "metric": "Metric",
        "period_start": "Period Start",
        "xbrl_tag": "XBRL Tag",
        "accession": "Accession Number",
        "filed_date": "Filing Date"
    })

    columns = [
        "Period End",
        "Metric",
        "Value ($B)",
        "XBRL Tag",
        "Filing Date",
        "Accession Number",
        "SEC Filing"
    ]

    st.dataframe(
        source_df[columns].round(2),
        column_config={
            "SEC Filing": st.column_config.LinkColumn(
                "Original SEC Filing",
                display_text="Open Filing"
            )
        },
        hide_index=True,
        width="stretch"
    )

    st.caption(
        "Sources are SEC XBRL facts. "
        "Filing dates and financial periods "
        "may differ because of later filings."
    )
