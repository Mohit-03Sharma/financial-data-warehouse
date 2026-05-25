import streamlit as st
import pandas as pd
import plotly.express as px
from google.cloud import bigquery

PROJECT = "cultivated-oven-497315-j1"
DATASET = "staging"

st.set_page_config(page_title="Financial Data Warehouse", layout="wide")

@st.cache_data(ttl=3600)
def run_query(sql):
    client = bigquery.Client(project=PROJECT)
    return client.query(sql).to_dataframe()

# sidebar navigation
page = st.sidebar.selectbox("Select Page", [
    "Sector Performance",
    "Economic Regime Analysis",
    "Pipeline Health"
])

if page == "Sector Performance":
    st.title("Sector Returns by Year")
    df = run_query(f"""
        SELECT year, sector,
            ROUND(AVG(daily_return_pct) * 252, 2) as annualized_return
        FROM `{PROJECT}.{DATASET}.fct_stock_performance`
        WHERE is_weekday = true AND sector IS NOT NULL
        GROUP BY year, sector
        ORDER BY year, sector
    """)
    fig = px.line(df, x="year", y="annualized_return", color="sector",
                  title="Annualized Returns by Sector (2010-Present)",
                  labels={"annualized_return": "Annualized Return (%)", "year": "Year"})
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(df)

elif page == "Economic Regime Analysis":
    st.title("Sector Performance by Economic Regime")
    df = run_query(f"""
        SELECT economic_regime, sector,
            ROUND(AVG(daily_return_pct) * 252, 2) as annualized_return,
            COUNT(*) as trading_days
        FROM `{PROJECT}.{DATASET}.fct_stock_performance`
        WHERE is_weekday = true AND economic_regime IS NOT NULL
        GROUP BY economic_regime, sector
        ORDER BY economic_regime, annualized_return DESC
    """)
    fig = px.bar(df, x="sector", y="annualized_return", color="economic_regime",
                 barmode="group",
                 title="How Sectors Perform in Different Economic Regimes",
                 labels={"annualized_return": "Annualized Return (%)", "sector": "Sector"})
    fig.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(df)

elif page == "Pipeline Health":
    st.title("Pipeline Health")
    df = run_query(f"""
        SELECT run_date, task_name, status, rows_processed,
            error_message, ROUND(duration_seconds, 2) as duration_seconds
        FROM `{PROJECT}.raw.pipeline_logs`
        ORDER BY logged_at DESC
        LIMIT 50
    """)
    if len(df) > 0:
        success_rate = len(df[df["status"] == "success"]) / len(df) * 100
        st.metric("Pipeline Success Rate", f"{success_rate:.1f}%")
    st.dataframe(df)