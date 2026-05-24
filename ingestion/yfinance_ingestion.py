import os
import time
import pandas as pd
import yfinance as yf
from google.cloud import storage, bigquery
from datetime import date

GCP_PROJECT = "cultivated-oven-497315-j1"
GCS_BUCKET = "fin-dw-raw-ms"
BQ_TABLE = "cultivated-oven-497315-j1.raw.stock_prices"
START_DATE = "2010-01-01"

# 50 tickers across 10 sectors
TICKERS = {
    "Technology": ["AAPL", "MSFT", "NVDA", "GOOGL", "META"],
    "Financials": ["JPM", "BAC", "GS", "WFC", "MS"],
    "Health Care": ["JNJ", "UNH", "PFE", "ABBV", "MRK"],
    "Energy": ["XOM", "CVX", "COP", "SLB", "EOG"],
    "Consumer Discretionary": ["AMZN", "WMT", "HD", "MCD", "NKE"],
    "Industrials": ["CAT", "BA", "HON", "UPS", "GE"],
    "Utilities": ["NEE", "DUK", "SO", "D", "AEP"],
    "Materials": ["LIN", "APD", "ECL", "NEM", "FCX"],
    "Real Estate": ["AMT", "PLD", "CCI", "EQIX", "SPG"],
    "Communication Services": ["VZ", "T", "CMCSA", "DIS", "NFLX"],
}

def fetch_all_tickers():
    # download ohlcv for all tickers, return single dataframe
    all_tickers = [t for sector in TICKERS.values() for t in sector]
    print(f"Downloading {len(all_tickers)} tickers from {START_DATE}...")
    
    dfs = []
    for ticker in all_tickers:
        try:
            df = yf.download(ticker, start=START_DATE, auto_adjust=True, progress=False)
            if df.empty:
                print(f"  No data for {ticker}, skipping")
                continue
            # flatten multi-level columns: ('Close', 'AAPL') -> 'close'
            df.columns = [c[0].lower() if isinstance(c, tuple) else c.lower() for c in df.columns]
            # date is the index — name it and reset
            df.index.name = "date"
            df = df.reset_index()
            df["ticker"] = ticker
            df["ingested_at"] = pd.Timestamp.now("UTC")
            df = df[["ticker", "date", "open", "high", "low", "close", "volume", "ingested_at"]]
            df = df.dropna(subset=["close"])
            df = df[df["close"] > 0]
            dfs.append(df)
            print(f"  {ticker}: {len(df)} rows")
            time.sleep(0.2)
        except Exception as e:
            print(f"  Error fetching {ticker}: {e}")
            continue
    
    return pd.concat(dfs, ignore_index=True)

def upload_to_gcs(df):
    # save full dataset to gcs as raw backup
    client = storage.Client()
    bucket = client.bucket(GCS_BUCKET)
    today = date.today().isoformat()
    path = f"stocks/all_tickers/{today}.csv"
    bucket.blob(path).upload_from_string(df.to_csv(index=False), content_type="text/csv")
    print(f"Uploaded {len(df)} rows to GCS at {path}")

def load_to_bigquery(df):
    # load to bigquery
    client = bigquery.Client(project=GCP_PROJECT)
    job_config = bigquery.LoadJobConfig(
        schema=[
            bigquery.SchemaField("ticker", "STRING"),
            bigquery.SchemaField("date", "DATE"),
            bigquery.SchemaField("open", "FLOAT64"),
            bigquery.SchemaField("high", "FLOAT64"),
            bigquery.SchemaField("low", "FLOAT64"),
            bigquery.SchemaField("close", "FLOAT64"),
            bigquery.SchemaField("volume", "INT64"),
            bigquery.SchemaField("ingested_at", "TIMESTAMP"),
        ],
        write_disposition="WRITE_APPEND",
    )
    job = client.load_table_from_dataframe(df, BQ_TABLE, job_config=job_config)
    job.result()
    print(f"Loaded {len(df)} rows to BigQuery")

def run():
    df = fetch_all_tickers()
    print(f"\nTotal rows fetched: {len(df)}")
    upload_to_gcs(df)
    load_to_bigquery(df)
    print("Stock ingestion complete.")

if __name__ == "__main__":
    run()