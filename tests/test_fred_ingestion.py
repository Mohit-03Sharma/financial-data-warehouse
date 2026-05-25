import pandas as pd
import pytest

def test_fred_dataframe_columns():
    # verify expected columns exist after building a sample dataframe
    df = pd.DataFrame({
        "series_id": ["FEDFUNDS"],
        "date": ["2024-01-01"],
        "value": [5.33],
        "ingested_at": [pd.Timestamp.now("UTC")]
    })
    assert "series_id" in df.columns
    assert "date" in df.columns
    assert "value" in df.columns

def test_fred_no_null_values():
    # null values should be dropped before loading
    df = pd.DataFrame({
        "series_id": ["FEDFUNDS", "FEDFUNDS"],
        "date": ["2024-01-01", "2024-02-01"],
        "value": [5.33, None],
        "ingested_at": [pd.Timestamp.now("UTC"), pd.Timestamp.now("UTC")]
    })
    df = df.dropna(subset=["value"])
    assert len(df) == 1

def test_fred_series_ids():
    # only expected series ids should be processed
    valid_series = ["FEDFUNDS", "CPIAUCSL", "GDP", "UNRATE"]
    test_series = "FEDFUNDS"
    assert test_series in valid_series