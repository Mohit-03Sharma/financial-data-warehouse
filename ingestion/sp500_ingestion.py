import pandas as pd
from google.cloud import bigquery
from datetime import date

GCP_PROJECT = "cultivated-oven-497315-j1"
BQ_TABLE = "cultivated-oven-497315-j1.raw.sp500_constituents"

def fetch_sp500():
    # pull s&p 500 table from wikipedia with browser header to avoid 403
    import requests
    from io import StringIO
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36"}
    response = requests.get(url, headers=headers)
    tables = pd.read_html(StringIO(response.text))
    df = tables[0]
    df = df.rename(columns={
        "Symbol": "ticker",
        "Security": "company_name",
        "GICS Sector": "sector",
        "GICS Sub-Industry": "sub_industry",
        "Date added": "date_added",
    })
    df = df[["ticker", "company_name", "sector", "sub_industry", "date_added"]]
    df["ticker"] = df["ticker"].str.upper().str.strip()
    df["date_added"] = pd.to_datetime(df["date_added"], errors="coerce").dt.date
    df["ingested_at"] = pd.Timestamp.now("UTC")
    df = df.dropna(subset=["ticker"])
    return df

def load_to_bigquery(df):
    client = bigquery.Client(project=GCP_PROJECT)
    job_config = bigquery.LoadJobConfig(
        schema=[
            bigquery.SchemaField("ticker", "STRING"),
            bigquery.SchemaField("company_name", "STRING"),
            bigquery.SchemaField("sector", "STRING"),
            bigquery.SchemaField("sub_industry", "STRING"),
            bigquery.SchemaField("date_added", "DATE"),
            bigquery.SchemaField("ingested_at", "TIMESTAMP"),
        ],
        write_disposition="WRITE_TRUNCATE",  # replace on every run
    )
    job = client.load_table_from_dataframe(df, BQ_TABLE, job_config=job_config)
    job.result()
    print(f"Loaded {len(df)} S&P 500 constituents to BigQuery")

def run():
    print("Fetching S&P 500 constituents from Wikipedia...")
    df = fetch_sp500()
    print(f"Fetched {len(df)} companies")
    load_to_bigquery(df)
    print("S&P 500 ingestion complete.")

if __name__ == "__main__":
    run()