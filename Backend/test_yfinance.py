#!/usr/bin/env python
import os
import sys
import django

# Django 설정
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Finflow.settings')
django.setup()

from stocks.services.yfinance_client import YFinanceClient
from stocks.models import Stock
import json

# 테스트
code = '005930'
stock = Stock.objects.filter(code=code).first()

if stock:
    print(f"Stock found: {stock.code} - {stock.name} - {stock.market}")
    data = YFinanceClient.get_realtime_price(code, stock.market)
    if data:
        print("\n=== Realtime Data ===")
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print("Failed to get realtime data")
else:
    print(f"Stock {code} not found in database")

# 인트라데이 테스트
print("\n=== Intraday Test ===")
if stock:
    intraday = YFinanceClient.get_intraday_prices(code, stock.market, interval='5m', days=1)
    print(f"Got {len(intraday)} data points")
    if intraday:
        print("First item:", json.dumps(intraday[0], indent=2, ensure_ascii=False))
