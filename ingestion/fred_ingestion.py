import os
import time
import pandas as pd
from fredapi import Fred
from google.cloud import storage, bigquery
from datetime import date

FRED_API_KEY = os.getenv("FRED_API_KEY")
GCP_PROJECT = "cultivated-oven-497315-j1"
GCS_BUCKET = "fin-dw-raw-ms"
BQ_TABLE = "cultivated-oven-497315-j1.raw.fred_economic_indicators"
SERIES = ["FEDFUNDS", "CPIAUCSL", "GDP", "UNRATE"]
START_DATE = "2010-01-01"

def fetch_series(fred, series_id):
    # pull data from FRED, return as dataframe
    data = fred.get_series(series_id, observation_start=START_DATE)
    df = data.reset_index()
    df.columns = ["date", "value"]
    df["series_id"] = series_id
    df["ingested_at"] = pd.Timestamp.now("UTC")
    df = df[["series_id", "date", "value", "ingested_at"]]
    df = df.dropna(subset=["value"])
    return df

def upload_to_gcs(df, series_id):
    # save csv to gcs as raw backup before loading to bigquery
    client = storage.Client()
    bucket = client.bucket(GCS_BUCKET)
    today = date.today().isoformat()
    path = f"fred/{series_id}/{today}.csv"
    bucket.blob(path).upload_from_string(df.to_csv(index=False), content_type="text/csv")
    print(f"Uploaded {series_id} to GCS at {path}")

def load_to_bigquery(df):
    # append rows to bigquery table
    client = bigquery.Client(project=GCP_PROJECT)
    job_config = bigquery.LoadJobConfig(
        schema=[
            bigquery.SchemaField("series_id", "STRING"),
            bigquery.SchemaField("date", "DATE"),
            bigquery.SchemaField("value", "FLOAT64"),
            bigquery.SchemaField("ingested_at", "TIMESTAMP"),
        ],
        write_disposition="WRITE_APPEND",
    )
    job = client.load_table_from_dataframe(df, BQ_TABLE, job_config=job_config)
    job.result()
    print(f"Loaded {len(df)} rows to BigQuery")

def run():
    fred = Fred(api_key=FRED_API_KEY)
    for series_id in SERIES:
        print(f"Fetching {series_id}...")
        df = fetch_series(fred, series_id)
        upload_to_gcs(df, series_id)
        load_to_bigquery(df)
        time.sleep(0.5)  # respect FRED rate limits
    print("FRED ingestion complete.")

if __name__ == "__main__":
    run()