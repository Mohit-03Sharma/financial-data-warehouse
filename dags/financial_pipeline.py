import os
import sys
import uuid
from datetime import datetime, timedelta, date
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.providers.google.cloud.sensors.gcs import GCSObjectExistenceSensor
from google.cloud import bigquery

# add ingestion folder to path so we can import our scripts
sys.path.insert(0, '/opt/airflow')

GCP_PROJECT = "cultivated-oven-497315-j1"
GCS_BUCKET = "fin-dw-raw-ms"

default_args = {
    'owner': 'mohit',
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'start_date': datetime(2026, 5, 24),
}

def log_pipeline_run(task_name, status, rows_processed=0, error_message=None, duration_seconds=0.0):
    # write a row to pipeline_logs table after each task
    client = bigquery.Client(project=GCP_PROJECT)
    table = f"{GCP_PROJECT}.raw.pipeline_logs"
    rows = [{
        "run_id": str(uuid.uuid4()),
        "run_date": date.today().isoformat(),
        "task_name": task_name,
        "status": status,
        "rows_processed": rows_processed,
        "error_message": error_message or "",
        "duration_seconds": duration_seconds,
        "logged_at": datetime.utcnow().isoformat(),
    }]
    client.insert_rows_json(table, rows)

def run_fred_ingestion():
    import time
    from ingestion.fred_ingestion import run
    start = time.time()
    try:
        run()
        duration = time.time() - start
        log_pipeline_run("ingest_fred", "success", rows_processed=651, duration_seconds=duration)
    except Exception as e:
        log_pipeline_run("ingest_fred", "failure", error_message=str(e))
        raise

def run_stock_ingestion():
    import time
    start = time.time()
    # stock data already loaded via local ingestion script
    # DAG task verifies data exists rather than re-downloading
    client = bigquery.Client(project=GCP_PROJECT)
    query = f"SELECT COUNT(*) as cnt FROM `{GCP_PROJECT}.raw.stock_prices`"
    result = list(client.query(query).result())
    count = result[0].cnt
    if count < 200000:
        raise ValueError(f"stock_prices has only {count} rows, expected 200000+")
    print(f"stock_prices verified: {count} rows")
    duration = time.time() - start
    log_pipeline_run("ingest_stocks", "success", rows_processed=count, duration_seconds=duration)

def run_sp500_ingestion():
    import time
    from ingestion.sp500_ingestion import run
    start = time.time()
    try:
        run()
        duration = time.time() - start
        log_pipeline_run("ingest_sp500", "success", rows_processed=503, duration_seconds=duration)
    except Exception as e:
        log_pipeline_run("ingest_sp500", "failure", error_message=str(e))
        raise

def verify_bq_counts():
    # check that all three raw tables have data
    import time
    start = time.time()
    client = bigquery.Client(project=GCP_PROJECT)
    checks = {
        "fred_economic_indicators": 600,
        "stock_prices": 200000,
        "sp500_constituents": 500,
    }
    for table, min_rows in checks.items():
        query = f"SELECT COUNT(*) as cnt FROM `{GCP_PROJECT}.raw.{table}`"
        result = list(client.query(query).result())
        count = result[0].cnt
        if count < min_rows:
            raise ValueError(f"{table} has only {count} rows, expected at least {min_rows}")
        print(f"{table}: {count} rows -- OK")
    duration = time.time() - start
    log_pipeline_run("verify_bq_counts", "success", duration_seconds=duration)

with DAG(
    dag_id="financial_pipeline",
    default_args=default_args,
    schedule_interval="@daily",
    catchup=False,
    tags=["finance", "data-warehouse"],
) as dag:

    ingest_fred = PythonOperator(
        task_id="ingest_fred",
        python_callable=run_fred_ingestion,
    )

    ingest_stocks = PythonOperator(
        task_id="ingest_stocks",
        python_callable=run_stock_ingestion,
    )

    ingest_sp500 = PythonOperator(
        task_id="ingest_sp500",
        python_callable=run_sp500_ingestion,
    )

    check_gcs = GCSObjectExistenceSensor(
        task_id="check_gcs_sensor",
        bucket=GCS_BUCKET,
        object=f"fred/FEDFUNDS/{date.today().isoformat()}.csv",
        timeout=300,
        poke_interval=30,
        mode="poke",
    )

    verify_counts = PythonOperator(
        task_id="verify_bq_counts",
        python_callable=verify_bq_counts,
    )

    # task dependency chain
    ingest_fred >> ingest_stocks >> ingest_sp500 >> check_gcs >> verify_counts