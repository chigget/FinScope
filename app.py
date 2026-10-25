
import streamlit as st
import pandas as pd
import sqlite3

from pathlib import Path
from contextlib import closing


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


# ===== Financial Metrics =====

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


# ===== Historical Charts =====

st.subheader("Historical Financial Performance")

df["Revenue ($B)"] = df["revenue"] / 1e9
df["Net Income ($B)"] = df["net_income"] / 1e9

st.line_chart(
    df,
    x="fiscal_year",
    y=["Revenue ($B)", "Net Income ($B)"]
)


# ===== Revenue Growth Chart =====

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
