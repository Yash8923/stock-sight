import requests
import pandas as pd
import yfinance as yf
from django.conf import settings

def fetch_stock_data_for_symbol(symbol):
    """
    Tries Alpha Vantage first, then Yahoo Finance as fallback.
    Returns a DataFrame if successful, else None.
    """
    # 1️⃣ Try Alpha Vantage
    try:
        url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={settings.ALPHA_VANTAGE_API_KEY}"
        response = requests.get(url)
        data = response.json()

        if "Time Series (Daily)" in data:
            daily_data = data["Time Series (Daily)"]
            df = pd.DataFrame.from_dict(daily_data, orient="index", dtype=float)
            df.rename(columns={
                "1. open": "Open",
                "2. high": "High",
                "3. low": "Low",
                "4. close": "Close",
                "5. volume": "Volume"
            }, inplace=True)
            df["Volume"] = df["Volume"].astype(int)
            df.index = pd.to_datetime(df.index)
            return df.sort_index()
    except Exception as e:
        print("Alpha Vantage failed:", e)

    # 2️⃣ Try Yahoo Finance (as fallback)
    try:
        fallback_symbol = symbol.replace(".NS","").replace(".BSE","")
        df = yf.download(fallback_symbol, period="60d", interval="1d")
        if not df.empty:
            return df
    except Exception as e:
        print("Yahoo Finance failed:", e)

    return None  # ❌ Nothing worked