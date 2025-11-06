#!/usr/bin/env python3
"""Find correct asset/liability concepts from Finnhub"""
import sys
import os
import requests
import json

sys.path.insert(0, os.path.dirname(__file__))
from config import Config

Config.init()
api_key = Config.FINNHUB_API_KEY or os.getenv('FINNHUB_API_KEY', '')

symbol = 'AAPL'
financials_url = f'https://finnhub.io/api/v1/stock/financials-reported?symbol={symbol}&token={api_key}'
response = requests.get(financials_url, timeout=10)
data = response.json()

if data.get('data'):
    report = data['data'][0].get('report', {})
    bs = report.get('bs', [])
    
    print("Balance Sheet concepts related to Assets:")
    for item in bs:
        concept = item.get('concept', '')
        label = item.get('label', '')
        value = item.get('value', 0)
        if 'asset' in concept.lower():
            print(f"  {concept:60s} | {label:50s} | ${value:,.0f}")
    
    print("\nBalance Sheet concepts related to Liabilities:")
    for item in bs:
        concept = item.get('concept', '')
        label = item.get('label', '')
        value = item.get('value', 0)
        if 'liabilit' in concept.lower():
            print(f"  {concept:60s} | {label:50s} | ${value:,.0f}")

