#!/usr/bin/env python3
"""
Debug script to see raw Finnhub API responses
"""
import sys
import os
import requests
import json

sys.path.insert(0, os.path.dirname(__file__))

from config import Config

Config.init()
api_key = Config.FINNHUB_API_KEY or os.getenv('FINNHUB_API_KEY', '')

if not api_key:
    print("❌ FINNHUB_API_KEY nie jest ustawiony")
    sys.exit(1)

symbol = 'AAPL'

print("="*80)
print(f"Debug Finnhub API - Raw Responses for {symbol}")
print("="*80)

# 1. Company Profile
print("\n1. Company Profile:")
print("-"*80)
profile_url = f"https://finnhub.io/api/v1/stock/profile2?symbol={symbol}&token={api_key}"
try:
    profile_response = requests.get(profile_url, timeout=10)
    print(f"Status: {profile_response.status_code}")
    if profile_response.status_code == 200:
        profile_data = profile_response.json()
        print(json.dumps(profile_data, indent=2))
    else:
        print(f"Error: {profile_response.text}")
except Exception as e:
    print(f"Exception: {e}")

# 2. Financials Reported
print("\n\n2. Financials Reported:")
print("-"*80)
financials_url = f"https://finnhub.io/api/v1/stock/financials-reported?symbol={symbol}&token={api_key}"
try:
    financials_response = requests.get(financials_url, timeout=10)
    print(f"Status: {financials_response.status_code}")
    if financials_response.status_code == 200:
        financials_data = financials_response.json()
        # Print first entry in detail
        if financials_data.get('data') and len(financials_data['data']) > 0:
            print(f"\nTotal reports: {len(financials_data['data'])}")
            first_report = financials_data['data'][0]
            print(f"\nFirst report keys: {list(first_report.keys())}")
            print(f"\nFirst report (first 2000 chars):")
            print(json.dumps(first_report, indent=2)[:2000])
            
            # Show report structure
            if 'report' in first_report:
                report = first_report['report']
                print(f"\nReport type: {type(report)}")
                if isinstance(report, list):
                    print(f"Report length: {len(report)}")
                    if len(report) > 0:
                        print(f"\nFirst report item (first 1000 chars):")
                        print(json.dumps(report[0], indent=2)[:1000])
                elif isinstance(report, dict):
                    print(f"Report keys: {list(report.keys())}")
                    print(f"\nReport (first 1000 chars):")
                    print(json.dumps(report, indent=2)[:1000])
        else:
            print("No data returned")
            print(json.dumps(financials_data, indent=2)[:500])
    else:
        print(f"Error: {financials_response.text}")
except Exception as e:
    print(f"Exception: {e}")

# 3. Company Basic Financials (alternative endpoint)
print("\n\n3. Company Basic Financials (Alternative Endpoint):")
print("-"*80)
basic_url = f"https://finnhub.io/api/v1/company-news?symbol={symbol}&from=2024-01-01&to=2024-12-31&token={api_key}"
# Actually, let's try the metrics endpoint
metrics_url = f"https://finnhub.io/api/v1/stock/metric?symbol={symbol}&metric=all&token={api_key}"
try:
    metrics_response = requests.get(metrics_url, timeout=10)
    print(f"Status: {metrics_response.status_code}")
    if metrics_response.status_code == 200:
        metrics_data = metrics_response.json()
        print(json.dumps(metrics_data, indent=2)[:2000])
    else:
        print(f"Error: {metrics_response.text}")
except Exception as e:
    print(f"Exception: {e}")

print("\n" + "="*80)

