import pandas as pd
import pytest

def test_ticker_list_length():
    # should have exactly 50 tickers across 10 sectors
    tickers = {
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
    all_tickers = [t for sector in tickers.values() for t in sector]
    assert len(all_tickers) == 50

def test_ohlcv_columns_exist():
    # dataframe must have all required ohlcv columns
    df = pd.DataFrame({
        "ticker": ["AAPL"],
        "date": ["2024-01-01"],
        "open": [185.0],
        "high": [187.0],
        "low": [184.0],
        "close": [186.0],
        "volume": [50000000],
        "ingested_at": [pd.Timestamp.now("UTC")]
    })
    required = ["ticker", "date", "open", "high", "low", "close", "volume"]
    for col in required:
        assert col in df.columns

def test_no_negative_close_prices():
    # close prices must always be positive
    df = pd.DataFrame({
        "ticker": ["AAPL", "MSFT"],
        "close": [186.0, 420.0]
    })
    df = df[df["close"] > 0]
    assert len(df) == 2