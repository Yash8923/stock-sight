import os
import django
import requests
import pandas as pd
from datetime import datetime, timedelta

# ✅ Set up Django environment manually before importing models
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "stock_prediction.settings")
django.setup()

from prediction.models import StockHistory
from django.core.management.base import BaseCommand
from django.conf import settings

API_KEY = settings.ALPHA_VANTAGE_API_KEY

class Command(BaseCommand):
    help = "Fetch and store historical stock data for multiple NSE stocks"

    def handle(self, *args, **kwargs):
        stock_symbols = [
            "INFY.NS", "TCS.NS", "RELIANCE.NS", "HDFCBANK.NS", "ICICIBANK.NS"
        ]

        for symbol in stock_symbols:
            print(f"📡 Fetching data for {symbol}...")
            self.fetch_and_store(symbol)

    def fetch_and_store(self, stock_symbol):
        url = (
            f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={stock_symbol}&apikey={API_KEY}"
        )

        try:
            response = requests.get(url)
            data = response.json()

            if "Time Series (Daily)" in data:
                records = []
                for date, values in data["Time Series (Daily)"].items():
                    records.append(StockHistory(
                        stock_symbol=stock_symbol,
                        date=datetime.strptime(date, "%Y-%m-%d").date(),
                        open_price=float(values["1. open"]),
                        high_price=float(values["2. high"]),
                        low_price=float(values["3. low"]),
                        close_price=float(values["4. close"]),
                        volume=int(values["5. volume"])
                    ))

                StockHistory.objects.bulk_create(records, ignore_conflicts=True)
                self.stdout.write(self.style.SUCCESS(f"✅ Data saved for {stock_symbol}"))

            else:
                self.stdout.write(self.style.WARNING(f"⚠️ No data found for {stock_symbol}"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error for {stock_symbol}: {str(e)}"))

