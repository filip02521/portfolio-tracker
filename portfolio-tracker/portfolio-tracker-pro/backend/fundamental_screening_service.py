#!/usr/bin/env python3
"""
Fundamental Screening Service - Automated Quantitative Investment Selection

Implements fully automated investment screening strategies based on:
- Piotroski F-Score (Quality + Value)
- Altman Z-Score (Bankruptcy Risk Filter)
- Magic Formula (ROIC + EBIT/EV)
- Accrual Ratio (Earnings Quality Control)
- VQ+ Strategy (Value + Quality with protective filters)
"""

import logging
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import requests
import os
from config import Config

logger = logging.getLogger(__name__)


class FundamentalScreeningService:
    """
    Service for automated fundamental analysis and stock screening
    based on quantitative models (F-Score, Z-Score, Magic Formula, etc.)
    """
    
    def __init__(self, market_data_service=None):
        self.market_data_service = market_data_service
        self.logger = logger
        
        # API Keys for fundamental data
        Config.init()  # Initialize Config to load environment variables
        self.finnhub_api_key = Config.FINNHUB_API_KEY or os.getenv('FINNHUB_API_KEY', '')
        self.alpha_vantage_api_key = Config.ALPHA_VANTAGE_API_KEY or os.getenv('ALPHA_VANTAGE_API_KEY', '')
        
        # Cache for fundamental data
        self._fundamental_cache = {}
        self._cache_ttl = 86400  # 24 hours
        
    def get_fundamental_data(self, symbol: str, exchange: str = 'US') -> Optional[Dict]:
        """
        Fetch fundamental financial data for a symbol.
        
        Tries multiple sources:
        1. Finnhub API (if available)
        2. Alpha Vantage (if available)
        3. Fallback to mock data for testing
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL', 'TSLA')
            exchange: Exchange code (default: 'US')
            
        Returns:
            Dict with financial data or None if unavailable
        """
        cache_key = f"{symbol}_{exchange}"
        if cache_key in self._fundamental_cache:
            cached_data, cached_time = self._fundamental_cache[cache_key]
            if (datetime.now() - cached_time).seconds < self._cache_ttl:
                return cached_data
        
        fundamental_data = None
        
        # Try Finnhub API
        if self.finnhub_api_key:
            try:
                fundamental_data = self._fetch_from_finnhub(symbol)
            except Exception as e:
                self.logger.warning(f"Finnhub API error for {symbol}: {e}")
        
        # Try Alpha Vantage as fallback
        if not fundamental_data and self.alpha_vantage_api_key:
            try:
                fundamental_data = self._fetch_from_alpha_vantage(symbol)
            except Exception as e:
                self.logger.warning(f"Alpha Vantage API error for {symbol}: {e}")
        
        # Fallback to mock data structure for testing
        if not fundamental_data:
            self.logger.debug(f"Using mock fundamental data for {symbol}")
            fundamental_data = self._get_mock_fundamental_data(symbol)
        
        if fundamental_data:
            self._fundamental_cache[cache_key] = (fundamental_data, datetime.now())
        
        return fundamental_data
    
    def get_fundamental_data_historical(self, symbol: str, year_offset: int = 1, exchange: str = 'US') -> Optional[Dict]:
        """
        Fetch fundamental financial data from a previous year.
        
        Args:
            symbol: Stock symbol
            year_offset: Number of years back (1 = previous year, 2 = 2 years ago, etc.)
            exchange: Exchange code (default: 'US')
            
        Returns:
            Dict with financial data from the specified year or None if unavailable
        """
        if year_offset < 1:
            year_offset = 1
        
        # Try Alpha Vantage first (has historical data in annualReports array)
        if self.alpha_vantage_api_key:
            try:
                return self._fetch_from_alpha_vantage_historical(symbol, year_offset)
            except Exception as e:
                self.logger.warning(f"Alpha Vantage historical data error for {symbol}: {e}")
        
        # Try Finnhub
        if self.finnhub_api_key:
            try:
                return self._fetch_from_finnhub_historical(symbol, year_offset)
            except Exception as e:
                self.logger.warning(f"Finnhub historical data error for {symbol}: {e}")
        
        return None
    
    def _fetch_from_alpha_vantage_historical(self, symbol: str, year_offset: int = 1) -> Optional[Dict]:
        """Fetch historical fundamental data from Alpha Vantage API"""
        try:
            # Income statement
            income_url = f"https://www.alphavantage.co/query?function=INCOME_STATEMENT&symbol={symbol}&apikey={self.alpha_vantage_api_key}"
            income_response = requests.get(income_url, timeout=10)
            if income_response.status_code != 200:
                return None
            income_data = income_response.json()
            
            # Balance sheet
            balance_url = f"https://www.alphavantage.co/query?function=BALANCE_SHEET&symbol={symbol}&apikey={self.alpha_vantage_api_key}"
            balance_response = requests.get(balance_url, timeout=10)
            if balance_response.status_code != 200:
                return None
            balance_data = balance_response.json()
            
            # Cash flow
            cashflow_url = f"https://www.alphavantage.co/query?function=CASH_FLOW&symbol={symbol}&apikey={self.alpha_vantage_api_key}"
            cashflow_response = requests.get(cashflow_url, timeout=10)
            if cashflow_response.status_code != 200:
                return None
            cashflow_data = cashflow_response.json()
            
            # Get overview for symbol info
            overview_url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={symbol}&apikey={self.alpha_vantage_api_key}"
            overview_response = requests.get(overview_url, timeout=10)
            overview_data = overview_response.json() if overview_response.status_code == 200 else {}
            
            # Extract data from year_offset position (0 = latest, 1 = previous year, etc.)
            annual_income = income_data.get('annualReports', [])
            annual_balance = balance_data.get('annualReports', [])
            annual_cashflow = cashflow_data.get('annualReports', [])
            
            if len(annual_income) <= year_offset or len(annual_balance) <= year_offset:
                return None
            
            # Use overview for current market cap (historical market cap not available)
            return self._parse_alpha_vantage_data(
                overview_data,
                {'annualReports': [annual_income[year_offset]]},
                {'annualReports': [annual_balance[year_offset]]},
                {'annualReports': [annual_cashflow[year_offset]] if len(annual_cashflow) > year_offset else []}
            )
            
        except Exception as e:
            self.logger.error(f"Error fetching historical data from Alpha Vantage: {e}")
            return None
    
    def _fetch_from_finnhub_historical(self, symbol: str, year_offset: int = 1) -> Optional[Dict]:
        """Fetch historical fundamental data from Finnhub API"""
        try:
            # Financials (income statement, balance sheet, cash flow)
            financials_url = f"https://finnhub.io/api/v1/stock/financials-reported?symbol={symbol}&token={self.finnhub_api_key}"
            financials_response = requests.get(financials_url, timeout=10)
            
            if financials_response.status_code != 200:
                return None
            
            financials_data = financials_response.json()
            
            # Get data from year_offset position
            if financials_data.get('data') and len(financials_data['data']) > year_offset:
                historical_data = financials_data['data'][year_offset]
                
                # Get company profile for basic info
                profile_url = f"https://finnhub.io/api/v1/stock/profile2?symbol={symbol}&token={self.finnhub_api_key}"
                profile_response = requests.get(profile_url, timeout=10)
                profile_data = profile_response.json() if profile_response.status_code == 200 else {}
                
                return self._parse_finnhub_data(profile_data, {'data': [historical_data]})
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error fetching historical data from Finnhub: {e}")
            return None
    
    def _fetch_from_finnhub(self, symbol: str) -> Optional[Dict]:
        """Fetch fundamental data from Finnhub API"""
        try:
            # Company profile
            profile_url = f"https://finnhub.io/api/v1/stock/profile2?symbol={symbol}&token={self.finnhub_api_key}"
            profile_response = requests.get(profile_url, timeout=10)
            
            if profile_response.status_code != 200:
                return None
            
            profile_data = profile_response.json()
            
            # Financials (income statement, balance sheet, cash flow)
            financials_url = f"https://finnhub.io/api/v1/stock/financials-reported?symbol={symbol}&token={self.finnhub_api_key}"
            financials_response = requests.get(financials_url, timeout=10)
            
            financials_data = financials_response.json() if financials_response.status_code == 200 else {}
            
            # Extract key metrics
            return self._parse_finnhub_data(profile_data, financials_data)
            
        except Exception as e:
            self.logger.error(f"Error fetching from Finnhub: {e}")
            return None
    
    def _fetch_from_alpha_vantage(self, symbol: str) -> Optional[Dict]:
        """Fetch fundamental data from Alpha Vantage API"""
        try:
            # Company overview
            overview_url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={symbol}&apikey={self.alpha_vantage_api_key}"
            overview_response = requests.get(overview_url, timeout=10)
            
            if overview_response.status_code != 200:
                return None
            
            overview_data = overview_response.json()
            
            # Income statement
            income_url = f"https://www.alphavantage.co/query?function=INCOME_STATEMENT&symbol={symbol}&apikey={self.alpha_vantage_api_key}"
            income_response = requests.get(income_url, timeout=10)
            income_data = income_response.json() if income_response.status_code == 200 else {}
            
            # Balance sheet
            balance_url = f"https://www.alphavantage.co/query?function=BALANCE_SHEET&symbol={symbol}&apikey={self.alpha_vantage_api_key}"
            balance_response = requests.get(balance_url, timeout=10)
            balance_data = balance_response.json() if balance_response.status_code == 200 else {}
            
            # Cash flow
            cashflow_url = f"https://www.alphavantage.co/query?function=CASH_FLOW&symbol={symbol}&apikey={self.alpha_vantage_api_key}"
            cashflow_response = requests.get(cashflow_url, timeout=10)
            cashflow_data = cashflow_response.json() if cashflow_response.status_code == 200 else {}
            
            return self._parse_alpha_vantage_data(overview_data, income_data, balance_data, cashflow_data)
            
        except Exception as e:
            self.logger.error(f"Error fetching from Alpha Vantage: {e}")
            return None
    
    def _parse_finnhub_data(self, profile_data: Dict, financials_data: Dict) -> Dict:
        """Parse Finnhub API response into standardized format"""
        # Extract latest financials if available
        latest_financials = {}
        
        # Ensure profile_data is a dict
        if not isinstance(profile_data, dict):
            profile_data = {}
        
        # Ensure financials_data is a dict
        if not isinstance(financials_data, dict):
            financials_data = {}
        
        if financials_data.get('data') and len(financials_data['data']) > 0:
            latest = financials_data['data'][0]
            if not isinstance(latest, dict):
                latest = {}
            
            # Finnhub returns report as dict with 'bs' (balance sheet), 'ic' (income statement), 'cf' (cash flow)
            report = latest.get('report', {})
            if not isinstance(report, dict):
                report = {}
            
            # Helper function to extract value from items list matching concepts
            def extract_value_exact(items, concept_exact, default=0):
                """Extract value for exact concept match (e.g., 'us-gaap_Assets')"""
                if not isinstance(items, list):
                    return default
                for item in items:
                    if not isinstance(item, dict):
                        continue
                    if item.get('concept', '') == concept_exact:
                        value = item.get('value', 0)
                        try:
                            return float(value) if value else default
                        except (ValueError, TypeError):
                            return default
                return default
            
            def extract_value(items, concepts, default=0, exclude_concepts=None):
                """Extract value from items list matching concepts, excluding certain patterns"""
                if not isinstance(items, list):
                    return default
                if exclude_concepts is None:
                    exclude_concepts = []
                
                candidates = []
                for item in items:
                    if not isinstance(item, dict):
                        continue
                    concept = item.get('concept', '').lower()
                    label = item.get('label', '').lower()
                    
                    # Skip if matches exclusion pattern
                    if any(excl in concept for excl in exclude_concepts):
                        continue
                    
                    # Check if matches any of the target concepts
                    for concept_key in concepts:
                        if concept_key in concept:
                            value = item.get('value', 0)
                            try:
                                value = float(value) if value else 0
                                # Prioritize items with "total" in label or concept
                                priority = 2 if 'total' in label or 'total' in concept else 1
                                candidates.append((priority, value))
                                break
                            except (ValueError, TypeError):
                                continue
                
                if candidates:
                    # Return highest priority, then largest value
                    candidates.sort(key=lambda x: (-x[0], -x[1]))
                    return candidates[0][1]
                return default
            
            # Parse Balance Sheet (bs)
            bs_items = report.get('bs', [])
            if isinstance(bs_items, list):
                # Use exact concept matches first (most reliable)
                latest_financials['total_assets'] = extract_value_exact(bs_items, 'us-gaap_Assets', 0)
                latest_financials['current_assets'] = extract_value_exact(bs_items, 'us-gaap_AssetsCurrent', 0)
                latest_financials['total_liabilities'] = extract_value_exact(bs_items, 'us-gaap_Liabilities', 0)
                latest_financials['current_liabilities'] = extract_value_exact(bs_items, 'us-gaap_LiabilitiesCurrent', 0)
                
                # Fallback to pattern matching if exact match fails
                if latest_financials['total_assets'] == 0:
                    # Look for "Assets" but NOT "AssetsCurrent" or "AssetsNoncurrent"
                    latest_financials['total_assets'] = extract_value(
                        bs_items, ['assets'], 0, exclude_concepts=['assetscurrent', 'assetsnoncurrent', 'otherassets']
                    )
                
                if latest_financials['current_assets'] == 0:
                    latest_financials['current_assets'] = extract_value(
                        bs_items, ['assetscurrent'], 0
                    )
                
                if latest_financials['total_liabilities'] == 0:
                    latest_financials['total_liabilities'] = extract_value(
                        bs_items, ['liabilities'], 0, exclude_concepts=['liabilitiescurrent', 'liabilitiesnoncurrent', 'otherliabilities']
                    )
                
                if latest_financials['current_liabilities'] == 0:
                    latest_financials['current_liabilities'] = extract_value(
                        bs_items, ['liabilitiescurrent'], 0
                    )
                
                latest_financials['long_term_debt'] = extract_value(
                    bs_items, ['longtermdebt', 'longtermdebtnetofcurrent'], latest_financials.get('long_term_debt', 0)
                )
                latest_financials['cash_and_cash_equivalents'] = extract_value(
                    bs_items, ['cashandcashequivalents', 'cashandequivalents'], latest_financials.get('cash_and_cash_equivalents', 0)
                )
                latest_financials['retained_earnings'] = extract_value(
                    bs_items, ['retainedearnings'], latest_financials.get('retained_earnings', 0)
                )
                latest_financials['total_stockholders_equity'] = extract_value(
                    bs_items, ['stockholdersequity', 'equity', 'shareholdersequity'], latest_financials.get('total_stockholders_equity', 0)
                )
            
            # Parse Income Statement (ic)
            ic_items = report.get('ic', [])
            if isinstance(ic_items, list):
                # Try exact concept match first for revenue (Net Sales)
                latest_financials['revenue'] = extract_value_exact(
                    ic_items, 'us-gaap_RevenueFromContractWithCustomerExcludingAssessedTax', 0
                )
                # Also try other revenue concepts
                if latest_financials['revenue'] == 0:
                    # Look for items with "Net sales" or "Revenue" in label, prefer largest
                    revenue_candidates = []
                    for item in ic_items:
                        if not isinstance(item, dict):
                            continue
                        concept = item.get('concept', '').lower()
                        label = item.get('label', '').lower()
                        value = item.get('value', 0)
                        try:
                            value = float(value) if value else 0
                        except (ValueError, TypeError):
                            continue
                        
                        # Look for revenue/sales concepts
                        if ('revenue' in concept or 'sales' in concept) and 'assessed' not in concept:
                            # Prioritize "net sales" or "revenue" in label
                            priority = 2 if ('net sales' in label or 'revenue' in label) else 1
                            revenue_candidates.append((priority, value))
                    
                    if revenue_candidates:
                        revenue_candidates.sort(key=lambda x: (-x[0], -x[1]))
                        latest_financials['revenue'] = revenue_candidates[0][1]
                
                # Fallback to pattern matching
                if latest_financials['revenue'] == 0:
                    latest_financials['revenue'] = extract_value(
                        ic_items, ['revenues', 'revenue', 'sales', 'netsales', 'totalrevenue'], 0,
                        exclude_concepts=['assessed']
                    )
                latest_financials['cogs'] = extract_value(
                    ic_items, ['costofrevenue', 'costofgoodssold', 'cogs'], latest_financials.get('cogs', 0)
                )
                latest_financials['gross_profit'] = extract_value(
                    ic_items, ['grossprofit', 'grossincome'], latest_financials.get('gross_profit', 0)
                )
                latest_financials['ebit'] = extract_value(
                    ic_items, ['operatingincomeloss', 'incomebeforetax', 'ebit', 'earningsbeforeinterestandtax'], latest_financials.get('ebit', 0)
                )
                latest_financials['net_income'] = extract_value(
                    ic_items, ['netincomeloss', 'netincome', 'netincometocommon'], latest_financials.get('net_income', 0)
                )
            
            # Parse Cash Flow (cf)
            cf_items = report.get('cf', [])
            if isinstance(cf_items, list):
                # Try multiple concepts for operating cash flow
                ocf_candidates = []
                for item in cf_items:
                    if not isinstance(item, dict):
                        continue
                    concept = item.get('concept', '').lower()
                    label = item.get('label', '').lower()
                    value = item.get('value', 0)
                    try:
                        value = float(value) if value else 0
                    except (ValueError, TypeError):
                        continue
                    
                    # Operating cash flow concepts
                    if any(term in concept for term in ['operatingcashflow', 'cashfromoperations', 'netcashprovidedbyoperatingactivities', 'operatingactivities']):
                        ocf_candidates.append(value)
                    elif any(term in label for term in ['operating', 'cash from operations']):
                        ocf_candidates.append(value)
                
                if ocf_candidates:
                    # Use the largest absolute value (most comprehensive)
                    latest_financials['operating_cash_flow'] = max(ocf_candidates, key=abs)
                else:
                    latest_financials['operating_cash_flow'] = 0
        
        revenue = profile_data.get('revenue', 0) or latest_financials.get('revenue', 0)
        cogs = latest_financials.get('cogs', 0)
        gross_profit = latest_financials.get('gross_profit', 0)
        # Calculate gross profit if not available but we have revenue and COGS
        if gross_profit == 0 and revenue > 0 and cogs > 0:
            gross_profit = revenue - cogs
        
        # Helper to safely convert values
        def safe_value(value, default=0):
            if value is None:
                return default
            if isinstance(value, dict):
                return default
            try:
                return float(value) if value else default
            except (ValueError, TypeError):
                return default
        
        # Revenue should already be extracted from ic_items above
        
        # Market Cap from Finnhub is in millions USD - ALWAYS convert to full USD
        # Finnhub API documentation states marketCapitalization is in millions
        market_cap_raw = profile_data.get('marketCapitalization', profile_data.get('market_cap', 0))
        if market_cap_raw and market_cap_raw > 0:
            market_cap_val = safe_value(market_cap_raw)
            # Finnhub always returns market cap in millions, so always multiply by 1,000,000
            # Exception: if the value is already huge (trillions), it might be in full units
            # But based on API docs, it's always in millions, so convert
            market_cap = market_cap_val * 1000000
        else:
            market_cap = 0
        
        # Share Outstanding from Finnhub is also in millions - ALWAYS convert
        # Finnhub API documentation states shareOutstanding is in millions
        shares_outstanding_raw = profile_data.get('shareOutstanding', profile_data.get('sharesOutstanding', 0))
        if shares_outstanding_raw and shares_outstanding_raw > 0:
            shares_val = safe_value(shares_outstanding_raw)
            # Finnhub always returns shares in millions, so always multiply by 1,000,000
            shares_outstanding = shares_val * 1000000
        else:
            shares_outstanding = 0
        
        return {
            'symbol': profile_data.get('ticker', profile_data.get('symbol', '')),
            'company_name': profile_data.get('name', profile_data.get('companyName', '')),
            'market_cap': market_cap,
            'total_assets': safe_value(latest_financials.get('total_assets', profile_data.get('totalAssets', 0))),
            'total_liabilities': safe_value(latest_financials.get('total_liabilities', profile_data.get('totalLiabilities', 0))),
            'net_income': safe_value(latest_financials.get('net_income', 0)),
            'operating_cash_flow': safe_value(latest_financials.get('operating_cash_flow', 0)),
            'revenue': safe_value(revenue),
            'ebit': safe_value(profile_data.get('ebit', latest_financials.get('ebit', 0))),
            'current_assets': safe_value(profile_data.get('currentAssets', latest_financials.get('current_assets', 0))),
            'current_liabilities': safe_value(profile_data.get('currentLiabilities', latest_financials.get('current_liabilities', 0))),
            'long_term_debt': safe_value(profile_data.get('longTermDebt', latest_financials.get('long_term_debt', 0))),
            'book_value': safe_value(profile_data.get('bookValue', profile_data.get('book_value', 0))),
            'shares_outstanding': shares_outstanding,
            'cogs': safe_value(cogs),
            'gross_profit': safe_value(gross_profit),
            'retained_earnings': safe_value(latest_financials.get('retained_earnings', 0)),
            'cash_and_cash_equivalents': safe_value(latest_financials.get('cash_and_cash_equivalents', 0)),
            'total_stockholders_equity': safe_value(latest_financials.get('total_stockholders_equity', 0)),
            'source': 'finnhub'
        }
    
    def _parse_alpha_vantage_data(self, overview: Dict, income: Dict, balance: Dict, cashflow: Dict) -> Dict:
        """Parse Alpha Vantage API response into standardized format"""
        # Extract latest annual data
        latest_income = income.get('annualReports', [{}])[0] if income.get('annualReports') else {}
        latest_balance = balance.get('annualReports', [{}])[0] if balance.get('annualReports') else {}
        latest_cashflow = cashflow.get('annualReports', [{}])[0] if cashflow.get('annualReports') else {}
        
        def safe_float(value, default=0.0):
            """Safely convert value to float, handling 'None' strings"""
            if value is None or value == 'None' or value == '':
                return default
            try:
                return float(value)
            except (ValueError, TypeError):
                return default
        
        revenue = safe_float(latest_income.get('totalRevenue', 0))
        cogs = safe_float(latest_income.get('costOfRevenue', 0))
        gross_profit = safe_float(latest_income.get('grossProfit', 0))
        # Calculate gross profit if not available but we have revenue and COGS
        if gross_profit == 0 and revenue > 0 and cogs > 0:
            gross_profit = revenue - cogs
        
        retained_earnings = safe_float(latest_balance.get('retainedEarnings', 0))
        cash = safe_float(latest_balance.get('cashAndCashEquivalentsAtCarryingValue', 0))
        total_equity = safe_float(latest_balance.get('totalStockholdersEquity', 0))
        
        # Fallback for retained earnings: if not available, estimate from total equity
        if retained_earnings == 0 and total_equity > 0:
            # Simplified: assume most of equity is retained earnings (common stock is usually small)
            retained_earnings = total_equity * 0.8  # Conservative estimate
        
        return {
            'symbol': overview.get('Symbol', ''),
            'company_name': overview.get('Name', ''),
            'market_cap': safe_float(overview.get('MarketCapitalization', 0)),
            'total_assets': safe_float(latest_balance.get('totalAssets', 0)),
            'total_liabilities': safe_float(latest_balance.get('totalLiabilities', 0)),
            'net_income': safe_float(latest_income.get('netIncome', 0)),
            'operating_cash_flow': safe_float(latest_cashflow.get('operatingCashflow', 0)),
            'revenue': revenue,
            'ebit': safe_float(latest_income.get('ebit', 0)),
            'current_assets': safe_float(latest_balance.get('totalCurrentAssets', 0)),
            'current_liabilities': safe_float(latest_balance.get('totalCurrentLiabilities', 0)),
            'long_term_debt': safe_float(latest_balance.get('longTermDebt', 0)),
            'book_value': safe_float(overview.get('BookValue', 0)),
            'shares_outstanding': safe_float(overview.get('SharesOutstanding', 0)),
            'cogs': cogs,
            'gross_profit': gross_profit,
            'retained_earnings': retained_earnings,
            'cash_and_cash_equivalents': cash,
            'total_stockholders_equity': total_equity,
            'source': 'alpha_vantage'
        }
    
    def _get_mock_fundamental_data(self, symbol: str) -> Dict:
        """Generate mock fundamental data for testing"""
        # This is a placeholder - in production, this should be removed or used only for testing
        np.random.seed(hash(symbol) % 2**32)
        
        base_assets = 1000000000  # $1B base
        assets = base_assets * (0.5 + np.random.random())
        revenue = assets * (0.5 + np.random.random() * 0.5)
        cogs = revenue * (0.4 + np.random.random() * 0.2)  # COGS typically 40-60% of revenue
        gross_profit = revenue - cogs
        
        return {
            'symbol': symbol,
            'company_name': f'{symbol} Corp',
            'market_cap': assets * (0.8 + np.random.random() * 0.4),
            'total_assets': assets,
            'total_liabilities': assets * (0.3 + np.random.random() * 0.3),
            'net_income': assets * (0.05 + np.random.random() * 0.1),
            'operating_cash_flow': assets * (0.08 + np.random.random() * 0.12),
            'revenue': revenue,
            'ebit': assets * (0.1 + np.random.random() * 0.1),
            'current_assets': assets * (0.2 + np.random.random() * 0.2),
            'current_liabilities': assets * (0.15 + np.random.random() * 0.15),
            'long_term_debt': assets * (0.1 + np.random.random() * 0.2),
            'book_value': assets * (0.4 + np.random.random() * 0.2),
            'shares_outstanding': 100000000 + np.random.randint(-50000000, 50000000),
            'cogs': cogs,
            'gross_profit': gross_profit,
            'retained_earnings': assets * (0.2 + np.random.random() * 0.2),
            'cash_and_cash_equivalents': assets * (0.05 + np.random.random() * 0.1),
            'total_stockholders_equity': assets * (0.4 + np.random.random() * 0.3),
            'source': 'mock'
        }
    
    def calculate_piotroski_f_score(self, symbol: str, current_data: Dict = None, previous_data: Dict = None) -> Dict:
        """
        Calculate Piotroski F-Score (0-9 points) for a company.
        
        F-Score consists of 9 binary criteria:
        - Profitability (4 points): Positive net income, positive ROA, positive CFO, CFO > Net Income
        - Leverage, Liquidity, Source of Funds (3 points): Decreasing leverage, increasing current ratio, no new equity issuance
        - Operating Efficiency (2 points): Increasing gross margin, increasing asset turnover
        
        Args:
            symbol: Stock symbol
            current_data: Current year financial data
            previous_data: Previous year financial data (for YoY comparisons)
            
        Returns:
            Dict with F-Score, breakdown, and details
        """
        if current_data is None:
            current_data = self.get_fundamental_data(symbol)
        
        if not current_data:
            return {
                'score': 0,
                'max_score': 9,
                'breakdown': {},
                'details': [],
                'error': 'No financial data available'
            }
        
        # Get previous year data if not provided
        if previous_data is None:
            # Fetch actual previous year data from API
            previous_data = self.get_fundamental_data_historical(symbol, year_offset=1)
            # Fallback to estimation if historical data not available
            if not previous_data:
                self.logger.debug(f"Historical data not available for {symbol}, using estimation")
                previous_data = self._estimate_previous_year_data(current_data)
        
        score = 0
        breakdown = {}
        details = []
        
        # === PROFITABILITY (4 points) ===
        
        # 1. Positive Net Income
        net_income_current = current_data.get('net_income', 0)
        if net_income_current > 0:
            score += 1
            breakdown['positive_net_income'] = 1
            details.append('✅ Positive Net Income')
        else:
            breakdown['positive_net_income'] = 0
            details.append('❌ Negative Net Income')
        
        # 2. Positive ROA (Return on Assets)
        total_assets_current = current_data.get('total_assets', 1)
        roa_current = (net_income_current / total_assets_current) * 100 if total_assets_current > 0 else 0
        if roa_current > 0:
            score += 1
            breakdown['positive_roa'] = 1
            details.append(f'✅ Positive ROA ({roa_current:.2f}%)')
        else:
            breakdown['positive_roa'] = 0
            details.append(f'❌ Negative ROA ({roa_current:.2f}%)')
        
        # 3. Positive Operating Cash Flow
        operating_cf_current = current_data.get('operating_cash_flow', 0)
        if operating_cf_current > 0:
            score += 1
            breakdown['positive_cfo'] = 1
            details.append('✅ Positive Operating Cash Flow')
        else:
            breakdown['positive_cfo'] = 0
            details.append('❌ Negative Operating Cash Flow')
        
        # 4. Cash Flow from Operations > Net Income (Quality of Earnings)
        if operating_cf_current > net_income_current and net_income_current > 0:
            score += 1
            breakdown['cfo_exceeds_net_income'] = 1
            details.append('✅ CFO > Net Income (High Quality Earnings)')
        else:
            breakdown['cfo_exceeds_net_income'] = 0
            details.append('❌ CFO ≤ Net Income (Lower Quality Earnings)')
        
        # === LEVERAGE, LIQUIDITY, SOURCE OF FUNDS (3 points) ===
        
        # 5. Decrease in Leverage (Long-term Debt / Total Assets)
        total_assets_previous = previous_data.get('total_assets', total_assets_current)
        long_term_debt_current = current_data.get('long_term_debt', 0)
        long_term_debt_previous = previous_data.get('long_term_debt', long_term_debt_current)
        
        leverage_current = (long_term_debt_current / total_assets_current) if total_assets_current > 0 else 0
        leverage_previous = (long_term_debt_previous / total_assets_previous) if total_assets_previous > 0 else 0
        
        if leverage_current < leverage_previous:
            score += 1
            breakdown['decreasing_leverage'] = 1
            details.append(f'✅ Decreasing Leverage ({leverage_current:.2%} vs {leverage_previous:.2%})')
        else:
            breakdown['decreasing_leverage'] = 0
            details.append(f'❌ Increasing/Stable Leverage ({leverage_current:.2%} vs {leverage_previous:.2%})')
        
        # 6. Increase in Current Ratio
        current_assets_current = current_data.get('current_assets', 0)
        current_liabilities_current = current_data.get('current_liabilities', 1)
        current_assets_previous = previous_data.get('current_assets', current_assets_current)
        current_liabilities_previous = previous_data.get('current_liabilities', current_liabilities_current)
        
        current_ratio_current = current_assets_current / current_liabilities_current if current_liabilities_current > 0 else 0
        current_ratio_previous = current_assets_previous / current_liabilities_previous if current_liabilities_previous > 0 else 0
        
        if current_ratio_current > current_ratio_previous:
            score += 1
            breakdown['increasing_current_ratio'] = 1
            details.append(f'✅ Increasing Current Ratio ({current_ratio_current:.2f} vs {current_ratio_previous:.2f})')
        else:
            breakdown['increasing_current_ratio'] = 0
            details.append(f'❌ Decreasing/Stable Current Ratio ({current_ratio_current:.2f} vs {current_ratio_previous:.2f})')
        
        # 7. No New Equity Issuance (simplified - assume no new shares if shares outstanding decreased or stayed same)
        shares_current = current_data.get('shares_outstanding', 0)
        shares_previous = previous_data.get('shares_outstanding', shares_current)
        
        if shares_current <= shares_previous:
            score += 1
            breakdown['no_new_equity'] = 1
            details.append('✅ No New Equity Issuance')
        else:
            breakdown['no_new_equity'] = 0
            details.append(f'❌ New Equity Issuance ({shares_current - shares_previous:.0f} new shares)')
        
        # === OPERATING EFFICIENCY (2 points) ===
        
        # 8. Increase in Gross Margin (TRUE Gross Margin: (Revenue - COGS) / Revenue)
        revenue_current = current_data.get('revenue', 0)
        revenue_previous = previous_data.get('revenue', revenue_current)
        
        # Calculate true gross margin: (Revenue - COGS) / Revenue
        cogs_current = current_data.get('cogs', 0)
        gross_profit_current = current_data.get('gross_profit', 0)
        if gross_profit_current == 0 and revenue_current > 0 and cogs_current > 0:
            gross_profit_current = revenue_current - cogs_current
        elif gross_profit_current == 0 and revenue_current > 0:
            # Fallback: estimate COGS as 50% of revenue if not available
            gross_profit_current = revenue_current * 0.5
        
        cogs_previous = previous_data.get('cogs', 0)
        gross_profit_previous = previous_data.get('gross_profit', 0)
        if gross_profit_previous == 0 and revenue_previous > 0 and cogs_previous > 0:
            gross_profit_previous = revenue_previous - cogs_previous
        elif gross_profit_previous == 0 and revenue_previous > 0:
            # Fallback: estimate COGS as 50% of revenue if not available
            gross_profit_previous = revenue_previous * 0.5
        
        gross_margin_current = (gross_profit_current / revenue_current) * 100 if revenue_current > 0 else 0
        gross_margin_previous = (gross_profit_previous / revenue_previous) * 100 if revenue_previous > 0 else 0
        
        if gross_margin_current > gross_margin_previous:
            score += 1
            breakdown['increasing_gross_margin'] = 1
            details.append(f'✅ Increasing Gross Margin ({gross_margin_current:.2f}% vs {gross_margin_previous:.2f}%)')
        else:
            breakdown['increasing_gross_margin'] = 0
            details.append(f'❌ Decreasing/Stable Gross Margin ({gross_margin_current:.2f}% vs {gross_margin_previous:.2f}%)')
        
        # 9. Increase in Asset Turnover
        asset_turnover_current = revenue_current / total_assets_current if total_assets_current > 0 else 0
        asset_turnover_previous = revenue_previous / total_assets_previous if total_assets_previous > 0 else 0
        
        if asset_turnover_current > asset_turnover_previous:
            score += 1
            breakdown['increasing_asset_turnover'] = 1
            details.append(f'✅ Increasing Asset Turnover ({asset_turnover_current:.2f} vs {asset_turnover_previous:.2f})')
        else:
            breakdown['increasing_asset_turnover'] = 0
            details.append(f'❌ Decreasing/Stable Asset Turnover ({asset_turnover_current:.2f} vs {asset_turnover_previous:.2f})')
        
        return {
            'score': score,
            'max_score': 9,
            'breakdown': breakdown,
            'details': details,
            'interpretation': self._interpret_f_score(score)
        }
    
    def _estimate_previous_year_data(self, current_data: Dict) -> Dict:
        """Estimate previous year data based on current data (simplified)"""
        # In production, fetch actual previous year data
        # For now, create a conservative estimate
        return {
            'total_assets': current_data.get('total_assets', 0) * 0.95,
            'total_liabilities': current_data.get('total_liabilities', 0) * 0.95,
            'net_income': current_data.get('net_income', 0) * 0.90,
            'operating_cash_flow': current_data.get('operating_cash_flow', 0) * 0.90,
            'revenue': current_data.get('revenue', 0) * 0.95,
            'ebit': current_data.get('ebit', 0) * 0.90,
            'current_assets': current_data.get('current_assets', 0) * 0.95,
            'current_liabilities': current_data.get('current_liabilities', 0) * 0.95,
            'long_term_debt': current_data.get('long_term_debt', 0) * 1.05,  # Assume higher debt before
            'shares_outstanding': current_data.get('shares_outstanding', 0) * 1.0
        }
    
    def _interpret_f_score(self, score: int) -> str:
        """Interpret F-Score value"""
        if score >= 8:
            return 'Excellent - Strong financial health and momentum'
        elif score >= 6:
            return 'Good - Solid financial fundamentals'
        elif score >= 4:
            return 'Fair - Moderate financial position'
        elif score >= 2:
            return 'Weak - Poor financial fundamentals'
        else:
            return 'Very Weak - High financial risk'
    
    def calculate_altman_z_score(self, symbol: str, financial_data: Dict = None) -> Dict:
        """
        Calculate Altman Z-Score for bankruptcy risk assessment.
        
        Z-Score = 1.2*A + 1.4*B + 3.3*C + 0.6*D + 1.0*E
        
        Where:
        - A = Working Capital / Total Assets
        - B = Retained Earnings / Total Assets
        - C = EBIT / Total Assets
        - D = Market Value of Equity / Total Liabilities
        - E = Sales / Total Assets
        
        Interpretation:
        - Z > 3.0: Safe zone (low bankruptcy risk)
        - 1.8 < Z < 3.0: Grey zone (moderate risk)
        - Z < 1.8: Distress zone (high bankruptcy risk)
        
        Args:
            symbol: Stock symbol
            financial_data: Financial data (if None, fetches automatically)
            
        Returns:
            Dict with Z-Score, components, and interpretation
        """
        if financial_data is None:
            financial_data = self.get_fundamental_data(symbol)
        
        if not financial_data:
            return {
                'z_score': 0,
                'components': {},
                'interpretation': 'No data available',
                'risk_level': 'unknown',
                'error': 'No financial data available'
            }
        
        total_assets = financial_data.get('total_assets', 1)
        total_liabilities = financial_data.get('total_liabilities', 0)
        current_assets = financial_data.get('current_assets', 0)
        current_liabilities = financial_data.get('current_liabilities', 0)
        ebit = financial_data.get('ebit', 0)
        revenue = financial_data.get('revenue', 0)
        market_cap = financial_data.get('market_cap', 0)
        net_income = financial_data.get('net_income', 0)
        
        # Calculate components
        # A: Working Capital / Total Assets
        working_capital = current_assets - current_liabilities
        A = (working_capital / total_assets) if total_assets > 0 else 0
        
        # B: Retained Earnings / Total Assets (TRUE Retained Earnings from balance sheet)
        retained_earnings = financial_data.get('retained_earnings', 0)
        # Retained Earnings can be negative (accumulated losses)
        # Don't override if it's negative - that's valid data
        if retained_earnings == 0:
            # Fallback: Retained Earnings = Total Equity - Common Stock (if available)
            total_equity = financial_data.get('total_stockholders_equity', 0)
            if total_equity > 0:
                # Simplified: assume most of equity is retained earnings (common stock is usually small)
                # But only if retained earnings wasn't explicitly negative
                retained_earnings = total_equity * 0.8  # Conservative estimate
            # If retained_earnings is still 0 and we have no equity data, use net income as proxy
            if retained_earnings == 0 and net_income > 0:
                retained_earnings = net_income
        B = (retained_earnings / total_assets) if total_assets > 0 else 0
        
        # C: EBIT / Total Assets
        C = (ebit / total_assets) if total_assets > 0 else 0
        
        # D: Market Value of Equity / Total Liabilities
        market_value_equity = market_cap
        D = (market_value_equity / total_liabilities) if total_liabilities > 0 else 0
        
        # E: Sales / Total Assets
        E = (revenue / total_assets) if total_assets > 0 else 0
        
        # Calculate Z-Score
        z_score = 1.2 * A + 1.4 * B + 3.3 * C + 0.6 * D + 1.0 * E
        
        # Determine risk level
        if z_score > 3.0:
            risk_level = 'safe'
            interpretation = 'Safe Zone - Low bankruptcy risk'
        elif z_score > 1.8:
            risk_level = 'moderate'
            interpretation = 'Grey Zone - Moderate bankruptcy risk'
        else:
            risk_level = 'high'
            interpretation = 'Distress Zone - High bankruptcy risk'
        
        return {
            'z_score': round(z_score, 2),
            'components': {
                'A': round(A, 4),
                'B': round(B, 4),
                'C': round(C, 4),
                'D': round(D, 4),
                'E': round(E, 4)
            },
            'interpretation': interpretation,
            'risk_level': risk_level,
            'recommendation': 'PASS' if z_score > 3.0 else ('CAUTION' if z_score > 1.8 else 'EXCLUDE')
        }
    
    def calculate_magic_formula_metrics(self, symbol: str, current_price: float = None, financial_data: Dict = None) -> Dict:
        """
        Calculate Magic Formula metrics (ROIC and EBIT/EV).
        
        Magic Formula ranks stocks by:
        1. Return on Invested Capital (ROIC) - Higher is better
        2. Earnings Yield (EBIT/EV) - Higher is better
        
        Args:
            symbol: Stock symbol
            current_price: Current stock price (if None, attempts to fetch)
            financial_data: Financial data (if None, fetches automatically)
            
        Returns:
            Dict with ROIC, EBIT/EV, and combined rank
        """
        if financial_data is None:
            financial_data = self.get_fundamental_data(symbol)
        
        if not financial_data:
            return {
                'roic': 0,
                'ebit_ev': 0,
                'combined_score': 0,
                'error': 'No financial data available'
            }
        
        # Get current price if not provided
        if current_price is None:
            if self.market_data_service:
                try:
                    # Try to get latest price - get_symbol_history_with_interval returns tuple (data, interval)
                    latest_data_result = self.market_data_service.get_symbol_history_with_interval(symbol, 1)
                    if isinstance(latest_data_result, tuple):
                        latest_data = latest_data_result[0]
                    else:
                        latest_data = latest_data_result
                    
                    if latest_data and isinstance(latest_data, list) and len(latest_data) > 0:
                        last_candle = latest_data[-1]
                        if isinstance(last_candle, dict):
                            price_value = last_candle.get('close', 0)
                            if price_value:
                                current_price = float(price_value)
                except Exception as e:
                    self.logger.debug(f"Error getting current price for {symbol}: {e}")
                    pass
            
            # Helper function to safely convert to float
            def safe_float(value, default=0.0):
                if value is None:
                    return default
                if isinstance(value, dict):
                    return default
                if isinstance(value, (int, float)):
                    return float(value)
                try:
                    return float(value)
                except (ValueError, TypeError):
                    return default
            
            if not current_price or current_price <= 0:
                # Estimate from market cap and shares
                market_cap = safe_float(financial_data.get('market_cap', 0))
                shares = safe_float(financial_data.get('shares_outstanding', 1))
                if market_cap and shares and shares > 0:
                    current_price = market_cap / shares
                else:
                    current_price = 0
        
        # Helper function to safely convert to float (reuse if already defined, otherwise define)
        try:
            safe_float
        except NameError:
            def safe_float(value, default=0.0):
                if value is None:
                    return default
                if isinstance(value, dict):
                    return default
                if isinstance(value, (int, float)):
                    return float(value)
                try:
                    return float(value)
                except (ValueError, TypeError):
                    return default
        
        # Ensure current_price is a float
        current_price = safe_float(current_price, 0.0)
        
        # Calculate ROIC
        # ROIC = EBIT / Invested Capital
        # Invested Capital = Total Assets - Current Liabilities - Cash (TRUE formula from report)
        ebit = safe_float(financial_data.get('ebit', 0))
        total_assets = safe_float(financial_data.get('total_assets', 1))
        current_liabilities = safe_float(financial_data.get('current_liabilities', 0))
        cash = safe_float(financial_data.get('cash_and_cash_equivalents', 0))
        # TRUE Invested Capital: Assets - Current Liabilities - Cash
        invested_capital = total_assets - current_liabilities - cash
        # Ensure invested capital is positive (if negative, use total assets as fallback)
        if invested_capital <= 0:
            invested_capital = total_assets if total_assets > 0 else 1
        roic = (ebit / invested_capital) * 100 if invested_capital > 0 else 0
        
        # Calculate EBIT/EV (Earnings Yield)
        # EV = Market Cap + Total Debt - Cash - TRUE formula from report
        market_cap = safe_float(financial_data.get('market_cap', 0))
        long_term_debt = safe_float(financial_data.get('long_term_debt', 0))
        current_liabilities = safe_float(financial_data.get('current_liabilities', 0))
        # Total Debt = Long-term Debt + Current Liabilities (simplified)
        # Note: In reality, we should use Total Liabilities, but for EV calculation,
        # we use debt specifically (long-term debt + short-term debt)
        # For simplicity, we'll use: Long-term Debt + (Current Liabilities as proxy for short-term debt)
        total_debt = long_term_debt + current_liabilities
        cash = safe_float(financial_data.get('cash_and_cash_equivalents', 0))
        # TRUE Enterprise Value: Market Cap + Debt - Cash
        enterprise_value = market_cap + total_debt - cash
        # Ensure enterprise value is positive
        if enterprise_value <= 0:
            enterprise_value = market_cap if market_cap > 0 else 1
        ebit_ev = (ebit / enterprise_value) * 100 if enterprise_value > 0 else 0
        
        # Combined score (normalized, higher is better)
        # Simple average for now (in production, use proper ranking)
        combined_score = (roic + ebit_ev) / 2
        
        # Ensure current_price is a float (already done above, but double-check)
        current_price = safe_float(current_price, 0.0)
        
        return {
            'roic': round(roic, 2),
            'ebit_ev': round(ebit_ev, 2),
            'combined_score': round(combined_score, 2),
            'current_price': round(current_price, 2) if current_price > 0 else 0.0,
            'enterprise_value': round(enterprise_value, 0),
            'invested_capital': round(invested_capital, 0)
        }
    
    def calculate_accrual_ratio(self, symbol: str, financial_data: Dict = None) -> Dict:
        """
        Calculate Accrual Ratio to detect earnings quality issues.
        
        Accrual Ratio = (Net Income - Operating Cash Flow) / Total Assets
        
        High accrual ratio suggests:
        - Aggressive accounting
        - Lower quality earnings
        - Potential manipulation
        
        Args:
            symbol: Stock symbol
            financial_data: Financial data (if None, fetches automatically)
            
        Returns:
            Dict with accrual ratio and interpretation
        """
        if financial_data is None:
            financial_data = self.get_fundamental_data(symbol)
        
        if not financial_data:
            return {
                'accrual_ratio': 0,
                'interpretation': 'No data available',
                'quality_flag': 'unknown',
                'error': 'No financial data available'
            }
        
        net_income = financial_data.get('net_income', 0)
        operating_cf = financial_data.get('operating_cash_flow', 0)
        total_assets = financial_data.get('total_assets', 1)
        
        accrual = net_income - operating_cf
        accrual_ratio = (accrual / total_assets) * 100 if total_assets > 0 else 0
        
        # Interpret results
        if accrual_ratio < -5:
            quality_flag = 'excellent'
            interpretation = 'Excellent - Cash flow significantly exceeds reported earnings (very high quality)'
        elif accrual_ratio < 0:
            quality_flag = 'good'
            interpretation = 'Good - Cash flow exceeds earnings (high quality)'
        elif accrual_ratio < 5:
            quality_flag = 'acceptable'
            interpretation = 'Acceptable - Moderate accruals (acceptable quality)'
        elif accrual_ratio < 10:
            quality_flag = 'warning'
            interpretation = 'Warning - High accruals suggest potential earnings quality issues'
        else:
            quality_flag = 'danger'
            interpretation = 'Danger - Very high accruals suggest aggressive accounting or manipulation'
        
        return {
            'accrual_ratio': round(accrual_ratio, 2),
            'accrual_amount': round(accrual, 0),
            'net_income': round(net_income, 0),
            'operating_cash_flow': round(operating_cf, 0),
            'interpretation': interpretation,
            'quality_flag': quality_flag,
            'recommendation': 'PASS' if accrual_ratio < 5 else ('CAUTION' if accrual_ratio < 10 else 'EXCLUDE')
        }
    
    def screen_vq_plus_strategy(self, symbols: List[str] = None, min_f_score: int = 7, 
                                max_z_score: float = 3.0, max_accrual_ratio: float = 5.0,
                                auto_universe: bool = False, universe_index: str = 'SP500',
                                value_percentile: float = 0.2) -> List[Dict]:
        """
        Screen stocks using VQ+ Strategy (Value + Quality with protective filters).
        
        According to the report (VI.1):
        1. Szeroki Skrining Value: Algorytmiczna selekcja uniwersum spółek nisko wycenianych (dolny kwintyl EBIT/EV)
        2. Automatyczny Filtr Jakości (F-Score): F-Score ≥ 7, 8, lub 9
        3. Automatyczne Filtry Ochronne: Z-Score > 3.0, Accrual Ratio < threshold
        4. Budowa Portfela i Rebalansowanie: Równe wagi, rebalansowanie roczne
        
        Args:
            symbols: List of stock symbols to screen (if None and auto_universe=True, uses universe)
            min_f_score: Minimum F-Score required (default: 7)
            max_z_score: Minimum Z-Score threshold (default: 3.0, we want > 3.0)
            max_accrual_ratio: Maximum Accrual Ratio allowed (default: 5.0)
            auto_universe: If True and symbols is None, automatically selects universe and ranks by EBIT/EV
            universe_index: Index to use for universe selection (default: 'SP500')
            value_percentile: Percentile for value screening (0.2 = bottom quintile = highest EBIT/EV)
            
        Returns:
            List of screened stocks with scores and rankings
        """
        # Step 1: If auto_universe and no symbols provided, get universe and rank by EBIT/EV
        if (symbols is None or len(symbols) == 0) and auto_universe:
            universe_symbols = self.get_universe_symbols(index=universe_index)
            # Rank universe by EBIT/EV (bottom percentile = highest EBIT/EV = lowest valuation)
            ranked_universe = self.rank_universe_by_ebit_ev(universe_symbols, percentile=value_percentile)
            symbols = [stock['symbol'] for stock in ranked_universe]
            self.logger.info(f"Auto-selected {len(symbols)} stocks from {universe_index} universe (bottom {value_percentile*100}% by EBIT/EV)")
        elif symbols is None:
            symbols = []
        
        results = []
        
        for symbol in symbols:
            try:
                # Get fundamental data
                financial_data = self.get_fundamental_data(symbol)
                if not financial_data:
                    continue
                
                # Validate fundamental data
                if not self._validate_fundamental_data(financial_data):
                    self.logger.debug(f"Skipping {symbol} due to invalid fundamental data")
                    continue
                
                # Calculate all metrics
                f_score_result = self.calculate_piotroski_f_score(symbol, financial_data)
                z_score_result = self.calculate_altman_z_score(symbol, financial_data)
                magic_formula = self.calculate_magic_formula_metrics(symbol, financial_data=financial_data)
                accrual = self.calculate_accrual_ratio(symbol, financial_data)
                
                f_score = f_score_result.get('score', 0)
                z_score = z_score_result.get('z_score', 0)
                accrual_ratio = accrual.get('accrual_ratio', 0)
                
                # Apply filters
                if f_score < min_f_score:
                    continue  # Filter: Low F-Score
                
                if z_score < 3.0:  # We want Z-Score > 3.0 (safe zone)
                    continue  # Filter: High bankruptcy risk
                
                if accrual_ratio > max_accrual_ratio:
                    continue  # Filter: Poor earnings quality
                
                # Calculate combined score (higher is better)
                # Weight: F-Score (40%), Magic Formula (40%), Z-Score (10%), Accrual (10%)
                normalized_f_score = (f_score / 9) * 100
                normalized_roic = min(magic_formula.get('roic', 0), 50)  # Cap at 50%
                normalized_ebit_ev = min(magic_formula.get('ebit_ev', 0), 30)  # Cap at 30%
                normalized_magic = ((normalized_roic + normalized_ebit_ev) / 2)
                normalized_z_score = min((z_score / 10) * 100, 100)  # Normalize Z-Score
                normalized_accrual = max(100 - (abs(accrual_ratio) * 10), 0)  # Lower accrual is better
                
                combined_score = (
                    normalized_f_score * 0.40 +
                    normalized_magic * 0.40 +
                    normalized_z_score * 0.10 +
                    normalized_accrual * 0.10
                )
                
                results.append({
                    'symbol': symbol,
                    'company_name': financial_data.get('company_name', symbol),
                    'f_score': f_score,
                    'z_score': z_score,
                    'roic': magic_formula.get('roic', 0),
                    'ebit_ev': magic_formula.get('ebit_ev', 0),
                    'accrual_ratio': accrual_ratio,
                    'combined_score': round(combined_score, 2),
                    'market_cap': financial_data.get('market_cap', 0),
                    'current_price': magic_formula.get('current_price', 0),
                    'f_score_details': f_score_result.get('details', []),
                    'z_score_risk': z_score_result.get('risk_level', 'unknown'),
                    'accrual_quality': accrual.get('quality_flag', 'unknown'),
                    'passes_all_filters': True
                })
                
            except Exception as e:
                self.logger.error(f"Error screening {symbol}: {e}")
                continue
        
        # Sort by combined score (descending)
        results.sort(key=lambda x: x['combined_score'], reverse=True)
        
        # Add ranking
        for i, result in enumerate(results, 1):
            result['rank'] = i
        
        return results
    
    def backtest_vq_plus_strategy(
        self,
        symbols: List[str] = None,
        start_date: str = None,
        end_date: str = None,
        initial_capital: float = 100000.0,
        rebalance_frequency: str = 'quarterly',  # 'quarterly' or 'yearly'
        max_positions: int = 20,
        min_f_score: int = 7,
        max_z_score: float = 3.0,
        max_accrual_ratio: float = 5.0,
        auto_universe: bool = False,
        universe_index: str = 'SP500',
        value_percentile: float = 0.2,
        transaction_cost: float = 0.001,  # 0.1% per trade (default)
        min_daily_volume: float = 1000000.0  # Minimum daily volume in USD (default: $1M)
    ) -> Dict:
        """
        Backtest the VQ+ Strategy on historical data.
        
        Strategy:
        1. Screen stocks using VQ+ filters at each rebalance date
        2. Select top N stocks (by combined_score)
        3. Allocate equal weights to each position
        4. Hold positions until next rebalance or until filters fail
        5. Rebalance quarterly or yearly
        
        Args:
            symbols: List of symbols to test (or None for auto_universe)
            start_date: Start date (ISO format 'YYYY-MM-DD')
            end_date: End date (ISO format 'YYYY-MM-DD')
            initial_capital: Initial capital (default: $100,000)
            rebalance_frequency: 'quarterly' or 'yearly' (default: 'quarterly')
            max_positions: Maximum number of positions in portfolio (default: 20)
            min_f_score: Minimum F-Score filter (default: 7)
            max_z_score: Minimum Z-Score threshold (default: 3.0)
            max_accrual_ratio: Maximum Accrual Ratio (default: 5.0)
            auto_universe: Auto-select universe if symbols is None
            universe_index: Index for universe selection (default: 'SP500')
            value_percentile: Value percentile for screening (default: 0.2)
            transaction_cost: Transaction cost as decimal (default: 0.001 = 0.1% per trade)
            min_daily_volume: Minimum daily volume in USD for liquidity filter (default: $1,000,000)
            
        Returns:
            Dict with backtest results:
            - total_return: Total return percentage
            - cagr: Compound Annual Growth Rate
            - sharpe_ratio: Sharpe Ratio
            - max_drawdown: Maximum drawdown percentage
            - win_rate: Percentage of profitable positions
            - profit_factor: Profit factor
            - total_trades: Total number of trades
            - winning_trades: Number of winning trades
            - equity_curve: List of portfolio values over time
            - trade_history: List of all trades
            - portfolio_compositions: Portfolio at each rebalance
        """
        try:
            # Parse dates
            if not start_date or not end_date:
                end_dt = datetime.now()
                start_dt = end_dt - timedelta(days=365 * 2)  # Default: 2 years
            else:
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            
            # Validate dates
            if start_dt >= end_dt:
                return {
                    'status': 'error',
                    'error': f'start_date ({start_date}) must be before end_date ({end_date})'
                }
            
            # Validate backtest period (max 10 years = 3650 days)
            max_period_days = 3650
            period_days = (end_dt - start_dt).days
            if period_days > max_period_days:
                return {
                    'status': 'error',
                    'error': f'Backtest period ({period_days} days) cannot exceed {max_period_days} days (10 years)'
                }
            
            # Validate symbols
            if symbols is not None:
                if not isinstance(symbols, list):
                    return {
                        'status': 'error',
                        'error': 'symbols must be a list'
                    }
                if len(symbols) == 0:
                    return {
                        'status': 'error',
                        'error': 'symbols list cannot be empty'
                    }
            
            # Validate parameters
            if initial_capital <= 0:
                return {
                    'status': 'error',
                    'error': f'initial_capital must be positive, got {initial_capital}'
                }
            
            if max_positions <= 0:
                return {
                    'status': 'error',
                    'error': f'max_positions must be positive, got {max_positions}'
                }
            
            if rebalance_frequency not in ['quarterly', 'yearly']:
                return {
                    'status': 'error',
                    'error': f'rebalance_frequency must be "quarterly" or "yearly", got "{rebalance_frequency}"'
                }
            
            # Validate transaction_cost
            if transaction_cost < 0 or transaction_cost > 0.1:  # Max 10%
                return {
                    'status': 'error',
                    'error': f'transaction_cost must be between 0 and 0.1 (0-10%), got {transaction_cost}'
                }
            
            # Adjust dates to trading days (skip weekends)
            start_dt = self._adjust_to_trading_day(start_dt)
            end_dt = self._adjust_to_trading_day(end_dt)
            
            # Generate rebalance dates
            rebalance_dates = self._generate_rebalance_dates(start_dt, end_dt, rebalance_frequency)
            
            if not rebalance_dates:
                return {
                    'status': 'error',
                    'error': 'No rebalance dates generated'
                }
            
            # Calculate total days for backtest to ensure we fetch enough historical data
            total_days = (end_dt - start_dt).days
            # Add buffer for safety (30 days)
            required_history_days = total_days + 30
            
            # Initialize backtest state
            cash = initial_capital
            positions = {}  # {symbol: {'shares': float, 'entry_price': float, 'entry_date': str}}
            equity_curve = []
            trade_history = []
            portfolio_compositions = []
            
            # Track metrics
            portfolio_values = [initial_capital]
            dates = [start_dt]
            peak_value = initial_capital
            max_drawdown = 0.0
            total_profit = 0.0
            total_loss = 0.0
            winning_trades_count = 0
            losing_trades_count = 0
            
            # Store backtest date range for _get_historical_price to use
            self._backtest_start_date = start_dt
            self._backtest_end_date = end_dt
            self._backtest_required_days = required_history_days
            
            # Process each rebalance period
            for rebalance_idx, rebalance_date in enumerate(rebalance_dates):
                self.logger.info(f"Rebalance {rebalance_idx + 1}/{len(rebalance_dates)}: {rebalance_date.strftime('%Y-%m-%d')}")
                
                # Step 1: Screen stocks at rebalance date
                # Adjust rebalance_date to trading day for price lookup
                trading_date = self._adjust_to_trading_day(rebalance_date)
                
                screened_stocks_raw = self.screen_vq_plus_strategy(
                    symbols=symbols,
                    min_f_score=min_f_score,
                    max_z_score=max_z_score,
                    max_accrual_ratio=max_accrual_ratio,
                    auto_universe=auto_universe,
                    universe_index=universe_index,
                    value_percentile=value_percentile
                )
                
                # Apply liquidity filter to screened stocks
                screened_stocks = []
                for stock in screened_stocks_raw:
                    symbol = stock.get('symbol')
                    if symbol:
                        # Check liquidity for this rebalance date
                        if self._check_liquidity(symbol, trading_date, min_daily_volume):
                            screened_stocks.append(stock)
                        else:
                            self.logger.debug(f"Excluding {symbol} from backtest due to insufficient liquidity")
                
                if not screened_stocks:
                    self.logger.warning(f"No stocks passed screening at {rebalance_date.strftime('%Y-%m-%d')}")
                    # Close all positions if no stocks pass
                    # trading_date already calculated above
                    positions_to_close = list(positions.items())
                    for symbol, position in positions_to_close:
                        exit_price = self._get_historical_price(symbol, trading_date)
                        if exit_price and isinstance(exit_price, (int, float)) and exit_price > 0:
                            cash_added, profit, transaction_cost_incurred = self._close_position(
                                symbol, position, exit_price, rebalance_date,
                                positions, trade_history, 'No stocks pass screening',
                                transaction_cost
                            )
                            cash += cash_added
                            total_transaction_costs += transaction_cost_incurred
                            if profit > 0:
                                total_profit += profit
                                winning_trades_count += 1
                            elif profit < 0:
                                total_loss += abs(profit)
                                losing_trades_count += 1
                            # Note: profit == 0 is neither winning nor losing
                    portfolio_compositions.append({
                        'date': rebalance_date.strftime('%Y-%m-%d'),
                        'positions': [],
                        'cash': cash,
                        'total_value': cash
                    })
                    portfolio_values.append(cash)
                    dates.append(rebalance_date)
                    continue
                
                # Step 2: Select top N stocks
                top_stocks = screened_stocks[:max_positions]
                target_symbols = [stock['symbol'] for stock in top_stocks]
                
                # Step 3: Close positions that no longer pass filters
                # trading_date already calculated in Step 1
                positions_to_check = list(positions.items())
                for symbol, position in positions_to_check:
                    if symbol not in target_symbols:
                        exit_price = self._get_historical_price(symbol, trading_date)
                        if exit_price and exit_price > 0:
                            cash_added, profit, transaction_cost_incurred = self._close_position(
                                symbol, position, exit_price, rebalance_date,
                                positions, trade_history, 'Filter failed at rebalance',
                                transaction_cost
                            )
                            cash += cash_added
                            total_transaction_costs += transaction_cost_incurred
                            if profit > 0:
                                total_profit += profit
                                winning_trades_count += 1
                            elif profit < 0:
                                total_loss += abs(profit)
                                losing_trades_count += 1
                
                # Step 4: Calculate total portfolio value
                # Use trading_date (already calculated in Step 3)
                portfolio_value = cash
                for symbol, position in positions.items():
                    current_price = self._get_historical_price(symbol, trading_date)
                    if current_price and current_price > 0:
                        portfolio_value += position['shares'] * current_price
                
                # Step 5: Rebalance to equal weights
                # First, close all existing positions to free up cash
                # IMPORTANT: Don't pop before calling _close_position - let it handle removal
                # Use trading_date (already calculated in Step 3)
                existing_symbols = list(positions.keys())
                for symbol in existing_symbols:
                    exit_price = self._get_historical_price(symbol, trading_date)
                    if exit_price and exit_price > 0:
                        # Get position data before closing
                        old_position = positions.get(symbol)
                        if old_position:
                            cash_added, profit, transaction_cost_incurred = self._close_position(
                                symbol, old_position, exit_price, rebalance_date,
                                positions, trade_history, 'Rebalance',
                                transaction_cost
                            )
                            cash += cash_added
                            total_transaction_costs += transaction_cost_incurred
                            if profit > 0:
                                total_profit += profit
                                winning_trades_count += 1
                            elif profit < 0:
                                total_loss += abs(profit)
                                losing_trades_count += 1
                            # Note: profit == 0 is neither winning nor losing
                
                # Recalculate portfolio value after closing positions
                portfolio_value = cash
                
                # Calculate target position value for each symbol (equal weighting)
                # If we don't have enough cash for all positions, reduce number of positions
                # to maintain equal weighting (better than partial positions)
                if target_symbols:
                    # Get entry prices for all target symbols first
                    # Use trading_date (already calculated in Step 3)
                    symbol_prices = {}
                    for symbol in target_symbols:
                        entry_price = self._get_historical_price(symbol, trading_date)
                        if entry_price and isinstance(entry_price, (int, float)) and entry_price > 0:
                            symbol_prices[symbol] = entry_price
                    
                    # Calculate how many positions we can afford with equal weighting
                    affordable_count = len(symbol_prices)
                    if affordable_count > 0:
                        # Try to allocate equally, reducing positions if needed
                        for attempt_count in range(affordable_count, 0, -1):
                            target_position_value = portfolio_value / attempt_count
                            
                            # Check if we can afford all positions at this target value
                            can_afford_all = True
                            for symbol, entry_price in symbol_prices.items():
                                shares = target_position_value / entry_price
                                position_value = shares * entry_price
                                if position_value > cash:
                                    can_afford_all = False
                                    break
                            
                            if can_afford_all:
                                # We can afford all positions, proceed with purchases
                                affordable_symbols = list(symbol_prices.keys())[:attempt_count]
                                for symbol in affordable_symbols:
                                    entry_price = symbol_prices[symbol]
                                    shares = target_position_value / entry_price
                                    position_value = shares * entry_price
                                    
                                    # Calculate transaction cost for opening position
                                    transaction_cost_amount = position_value * transaction_cost if transaction_cost > 0 else 0.0
                                    total_cost = position_value + transaction_cost_amount
                                    
                                    if cash >= total_cost:
                                        positions[symbol] = {
                                            'shares': shares,
                                            'entry_price': entry_price,
                                            'entry_date': rebalance_date.strftime('%Y-%m-%d')
                                        }
                                        cash -= total_cost
                                        total_transaction_costs += transaction_cost_amount
                                        
                                        trade_history.append({
                                            'date': rebalance_date.strftime('%Y-%m-%d'),
                                            'action': 'buy',
                                            'symbol': symbol,
                                            'price': entry_price,
                                            'shares': shares,
                                            'value': position_value,
                                            'transaction_cost': round(transaction_cost_amount, 2),
                                            'reason': 'VQ+ rebalance'
                                        })
                                break
                        else:
                            # If we can't afford even one position at equal weight,
                            # allocate remaining cash proportionally (fallback)
                            self.logger.warning(f"Cannot afford equal-weight positions, using proportional allocation")
                            remaining_cash = cash
                            for symbol, entry_price in list(symbol_prices.items()):
                                if remaining_cash <= 0:
                                    break
                                shares = remaining_cash / entry_price
                                if shares > 0:
                                    position_value = shares * entry_price
                                    # Calculate transaction cost
                                    transaction_cost_amount = position_value * transaction_cost if transaction_cost > 0 else 0.0
                                    total_cost = position_value + transaction_cost_amount
                                    
                                    if remaining_cash >= total_cost:
                                        positions[symbol] = {
                                            'shares': shares,
                                            'entry_price': entry_price,
                                            'entry_date': rebalance_date.strftime('%Y-%m-%d')
                                        }
                                        cash -= total_cost
                                        total_transaction_costs += transaction_cost_amount
                                        remaining_cash -= total_cost
                                        
                                        trade_history.append({
                                            'date': rebalance_date.strftime('%Y-%m-%d'),
                                            'action': 'buy',
                                            'symbol': symbol,
                                            'price': entry_price,
                                            'shares': shares,
                                            'value': position_value,
                                            'transaction_cost': round(transaction_cost_amount, 2),
                                            'reason': 'VQ+ rebalance (proportional)'
                                        })
                
                # Recalculate portfolio value after rebalancing
                # Use trading_date (already calculated in Step 1)
                portfolio_value = cash
                for symbol, position in positions.items():
                    current_price = self._get_historical_price(symbol, trading_date)
                    if current_price and isinstance(current_price, (int, float)) and current_price > 0:
                        portfolio_value += position['shares'] * current_price
                
                # Step 6: Update portfolio composition
                # Use trading_date (already calculated in Step 1)
                current_positions = []
                for symbol, position in positions.items():
                    current_price = self._get_historical_price(symbol, trading_date)
                    if current_price and isinstance(current_price, (int, float)) and current_price > 0:
                        current_positions.append({
                            'symbol': symbol,
                            'shares': position['shares'],
                            'entry_price': position['entry_price'],
                            'current_price': current_price,
                            'value': position['shares'] * current_price,
                            'return_pct': ((current_price - position['entry_price']) / position['entry_price']) * 100 if position['entry_price'] > 0 else 0
                        })
                
                portfolio_compositions.append({
                    'date': rebalance_date.strftime('%Y-%m-%d'),
                    'positions': current_positions,
                    'cash': cash,
                    'total_value': portfolio_value
                })
                
                # Update metrics
                portfolio_values.append(portfolio_value)
                dates.append(rebalance_date)
                
                if portfolio_value > peak_value:
                    peak_value = portfolio_value
                
                drawdown = ((peak_value - portfolio_value) / peak_value) * 100 if peak_value > 0 else 0
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
                
                # Log daily portfolio value (for equity curve)
                equity_curve.append({
                    'date': rebalance_date.strftime('%Y-%m-%d'),
                    'value': portfolio_value
                })
                
                # Log rebalance summary for debugging
                self.logger.debug(
                    f"Rebalance {rebalance_idx + 1} complete - Portfolio Value: ${portfolio_value:,.2f}, "
                    f"Cash: ${cash:,.2f}, Positions: {len(positions)}, "
                    f"Total Profit so far: ${total_profit:,.2f}, Total Loss so far: ${total_loss:,.2f}"
                )
            
            # Close all positions at end
            final_date = end_dt
            final_positions_list = list(positions.items())  # Create copy before iteration
            for symbol, position in final_positions_list:
                exit_price = self._get_historical_price(symbol, final_date)
                if exit_price and isinstance(exit_price, (int, float)) and exit_price > 0:
                    cash_added, profit, transaction_cost_incurred = self._close_position(
                        symbol, position, exit_price, final_date,
                        positions, trade_history, 'End of backtest',
                        transaction_cost
                    )
                    cash += cash_added
                    total_transaction_costs += transaction_cost_incurred
                    if profit > 0:
                        total_profit += profit
                        winning_trades_count += 1
                    elif profit < 0:
                        total_loss += abs(profit)
                        losing_trades_count += 1
                    # Note: profit == 0 is neither winning nor losing
            
            # Calculate final portfolio value
            # After closing all positions, final value is just the cash
            # (positions dict should be empty now, but double-check)
            final_portfolio_value = cash
            if positions:
                # If there are any remaining positions (shouldn't happen, but safety check)
                self.logger.warning(f"Remaining positions after closing: {list(positions.keys())}")
                for symbol, position in positions.items():
                    exit_price = self._get_historical_price(symbol, final_date)
                    if exit_price and isinstance(exit_price, (int, float)) and exit_price > 0:
                        final_portfolio_value += position['shares'] * exit_price
            
            portfolio_values.append(final_portfolio_value)
            dates.append(final_date)
            equity_curve.append({
                'date': final_date.strftime('%Y-%m-%d'),
                'value': final_portfolio_value
            })
            
            # Clean up backtest state variables
            if hasattr(self, '_backtest_start_date'):
                delattr(self, '_backtest_start_date')
            if hasattr(self, '_backtest_end_date'):
                delattr(self, '_backtest_end_date')
            if hasattr(self, '_backtest_required_days'):
                delattr(self, '_backtest_required_days')
            
            # Calculate performance metrics
            total_return = ((final_portfolio_value - initial_capital) / initial_capital) * 100 if initial_capital > 0 else 0
            
            # Log final metrics for debugging
            self.logger.info(
                f"Backtest completed - Initial: ${initial_capital:,.2f}, Final: ${final_portfolio_value:,.2f}, "
                f"Return: {total_return:.2f}%, Trades: {len(trade_history)}, "
                f"Winners: {winning_trades_count}, Losers: {losing_trades_count}, "
                f"Total Profit: ${total_profit:,.2f}, Total Loss: ${total_loss:,.2f}, "
                f"Total Transaction Costs: ${total_transaction_costs:,.2f}"
            )
            
            # Calculate CAGR
            years = (end_dt - start_dt).days / 365.0
            if years > 0 and initial_capital > 0:
                cagr = (((final_portfolio_value / initial_capital) ** (1.0 / years)) - 1) * 100
            else:
                cagr = 0.0
            
            # Calculate Sharpe Ratio (simplified - assumes risk-free rate = 0)
            if len(portfolio_values) > 1:
                returns = []
                for i in range(1, len(portfolio_values)):
                    if portfolio_values[i-1] > 0:
                        ret = ((portfolio_values[i] - portfolio_values[i-1]) / portfolio_values[i-1]) * 100
                        returns.append(ret)
                
                if returns:
                    avg_return = sum(returns) / len(returns)
                    variance = sum([(r - avg_return) ** 2 for r in returns]) / len(returns)
                    std_dev = variance ** 0.5
                    sharpe_ratio = (avg_return / std_dev) if std_dev > 0 else 0.0
                else:
                    sharpe_ratio = 0.0
            else:
                sharpe_ratio = 0.0
            
            # Calculate Win Rate
            total_trades_count = winning_trades_count + losing_trades_count
            win_rate = (winning_trades_count / total_trades_count * 100) if total_trades_count > 0 else 0.0
            
            # Calculate Profit Factor
            profit_factor = (total_profit / total_loss) if total_loss > 0 else (total_profit if total_profit > 0 else 0.0)
            
            return {
                'status': 'success',
                'total_return': round(total_return, 2),
                'cagr': round(cagr, 2),
                'sharpe_ratio': round(sharpe_ratio, 3),
                'max_drawdown': round(max_drawdown, 2),
                'win_rate': round(win_rate, 2),
                'profit_factor': round(profit_factor, 2),
                'total_trades': total_trades_count,
                'winning_trades': winning_trades_count,
                'losing_trades': losing_trades_count,
                'initial_capital': initial_capital,
                'final_value': round(final_portfolio_value, 2),
                'equity_curve': equity_curve,
                'trade_history': trade_history,
                'portfolio_compositions': portfolio_compositions,
                'rebalance_dates': [d.strftime('%Y-%m-%d') for d in rebalance_dates],
                'parameters': {
                    'rebalance_frequency': rebalance_frequency,
                    'max_positions': max_positions,
                    'min_f_score': min_f_score,
                    'max_z_score': max_z_score,
                    'max_accrual_ratio': max_accrual_ratio
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error in VQ+ backtest: {e}", exc_info=True)
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _generate_rebalance_dates(self, start_date: datetime, end_date: datetime, frequency: str) -> List[datetime]:
        """Generate rebalance dates based on frequency"""
        dates = []
        current = start_date
        
        if frequency == 'quarterly':
            # Rebalance every 3 months
            from dateutil.relativedelta import relativedelta
            try:
                while current <= end_date:
                    dates.append(current)
                    current = current + relativedelta(months=3)
                    if current > end_date:
                        break
            except ImportError:
                # Fallback if dateutil not available
                while current <= end_date:
                    dates.append(current)
                    # Add 3 months manually
                    new_month = current.month + 3
                    new_year = current.year
                    if new_month > 12:
                        new_year += 1
                        new_month -= 12
                    try:
                        current = current.replace(year=new_year, month=new_month)
                    except ValueError:
                        # Handle invalid date (e.g., Feb 30)
                        if new_month == 2:
                            current = current.replace(year=new_year, month=3, day=1)
                        else:
                            current = current.replace(year=new_year, month=new_month, day=1)
                    if current > end_date:
                        break
        elif frequency == 'yearly':
            # Rebalance every year
            while current <= end_date:
                dates.append(current)
                try:
                    current = current.replace(year=current.year + 1)
                except ValueError:
                    # Handle leap year (Feb 29)
                    current = current.replace(year=current.year + 1, month=3, day=1)
                if current > end_date:
                    break
        else:
            # Default: quarterly
            return self._generate_rebalance_dates(start_date, end_date, 'quarterly')
        
        return dates
    
    def _adjust_to_trading_day(self, date: datetime) -> datetime:
        """
        Adjust date to nearest trading day (skip weekends).
        
        Args:
            date: Date to adjust
            
        Returns:
            Adjusted date (weekday, or previous Friday if weekend)
        """
        # Simple implementation: skip weekends
        # If Saturday (5) or Sunday (6), move to previous Friday
        adjusted = date
        while adjusted.weekday() >= 5:  # Saturday = 5, Sunday = 6
            adjusted -= timedelta(days=1)
        return adjusted
    
    def _validate_fundamental_data(self, data: Dict) -> bool:
        """
        Validate fundamental data for sanity checks.
        
        Args:
            data: Fundamental data dictionary
            
        Returns:
            True if data is valid, False otherwise
        """
        if not data or not isinstance(data, dict):
            return False
        
        # Check for negative total assets (shouldn't happen)
        total_assets = data.get('total_assets', 0)
        if total_assets is not None and total_assets < 0:
            self.logger.warning(f"Invalid fundamental data: negative total_assets ({total_assets})")
            return False
        
        # Check for unrealistic revenue (negative is sometimes valid for losses, but very negative is suspicious)
        revenue = data.get('revenue', 0)
        if revenue is not None and revenue < -1e10:  # More than -$10 billion is suspicious
            self.logger.warning(f"Invalid fundamental data: unrealistic revenue ({revenue})")
            return False
        
        # Check for unrealistic market cap
        market_cap = data.get('market_cap', 0)
        if market_cap is not None and market_cap < 0:
            self.logger.warning(f"Invalid fundamental data: negative market_cap ({market_cap})")
            return False
        
        # Check for unrealistic shares outstanding
        shares = data.get('shares_outstanding', 0)
        if shares is not None and (shares < 0 or shares > 1e15):  # More than 1 quadrillion shares is unrealistic
            self.logger.warning(f"Invalid fundamental data: unrealistic shares_outstanding ({shares})")
            return False
        
        # Check for division by zero risks (total_assets should be positive for most calculations)
        if total_assets is not None and total_assets == 0:
            # Zero assets might be valid for some companies, but skip for screening
            self.logger.debug(f"Fundamental data has zero total_assets, skipping for screening")
            return False
        
        return True
    
    def _check_liquidity(self, symbol: str, date: datetime, min_volume: float = 1000000.0) -> bool:
        """
        Check if symbol has sufficient liquidity (daily volume).
        
        Args:
            symbol: Stock symbol
            date: Date to check liquidity
            min_volume: Minimum daily volume in USD
            
        Returns:
            True if liquidity is sufficient, False otherwise
        """
        if not self.market_data_service:
            # If no market data service, assume liquidity is OK (can't check)
            return True
        
        try:
            # Get historical data for the date (use a small window around the date)
            historical_data = self.market_data_service.get_symbol_history(symbol, days=30)
            
            if not historical_data or not isinstance(historical_data, list):
                # If we can't get data, assume liquidity is OK to avoid false negatives
                self.logger.debug(f"Could not fetch volume data for {symbol} on {date}, assuming liquidity OK")
                return True
            
            # Find volume for the target date or closest date
            target_date = date.date() if isinstance(date, datetime) else date
            closest_volume = None
            min_diff = timedelta(days=30)
            
            for candle in historical_data:
                if not isinstance(candle, dict):
                    continue
                
                candle_date_str = candle.get('timestamp', candle.get('date', ''))
                if not candle_date_str:
                    continue
                
                try:
                    if isinstance(candle_date_str, str):
                        if 'T' in candle_date_str:
                            candle_dt = datetime.fromisoformat(candle_date_str.replace('Z', '+00:00'))
                        else:
                            try:
                                candle_dt = datetime.strptime(candle_date_str, '%Y-%m-%d')
                            except ValueError:
                                continue
                    else:
                        continue
                    
                    candle_date = candle_dt.date()
                    volume_value = candle.get('volume', 0)
                    price_value = candle.get('close', candle.get('price', 0))
                    
                    if not volume_value or not price_value:
                        continue
                    
                    try:
                        volume = float(volume_value)
                        price = float(price_value)
                        
                        # Calculate volume in USD (volume * price)
                        volume_usd = volume * price if volume > 0 and price > 0 else 0
                        
                        # Check if this is the target date or closest
                        diff = abs(candle_date - target_date)
                        if diff < min_diff:
                            min_diff = diff
                            closest_volume = volume_usd
                    except (ValueError, TypeError):
                        continue
                except Exception:
                    continue
            
            # Check if closest volume meets minimum
            if closest_volume is not None:
                if min_diff <= timedelta(days=5):  # Within 5 days is acceptable
                    liquidity_ok = closest_volume >= min_volume
                    if not liquidity_ok:
                        self.logger.debug(
                            f"Insufficient liquidity for {symbol} on {target_date}: "
                            f"${closest_volume:,.0f} < ${min_volume:,.0f}"
                        )
                    return liquidity_ok
                else:
                    # Date is too far, assume OK
                    self.logger.debug(f"Volume data for {symbol} is too far from {target_date}, assuming liquidity OK")
                    return True
            else:
                # No volume data found, assume OK to avoid false negatives
                self.logger.debug(f"No volume data found for {symbol} on {target_date}, assuming liquidity OK")
                return True
        
        except Exception as e:
            self.logger.warning(f"Error checking liquidity for {symbol} on {date}: {e}")
            # On error, assume liquidity is OK to avoid false negatives
            return True
    
    def _get_historical_price(self, symbol: str, date: datetime) -> Optional[float]:
        """
        Get historical price for a symbol on a specific date.
        
        If called during backtest (backtest date range is set), fetches enough data
        to cover the entire backtest period. Otherwise, fetches last 365 days.
        """
        if not self.market_data_service:
            return None
        
        try:
            # If we're in a backtest, fetch enough data to cover the entire period
            # Otherwise, fetch last 365 days (default behavior)
            if hasattr(self, '_backtest_required_days') and self._backtest_required_days:
                # Use the required days from backtest
                days_to_fetch = max(self._backtest_required_days, 365)
                # Also ensure we fetch from at least the requested date (in case date is older)
                if isinstance(date, datetime):
                    days_since_date = (datetime.now().date() - date.date()).days
                    if days_since_date > 0:
                        days_to_fetch = max(days_to_fetch, days_since_date + 30)  # Add buffer
                # Cap at reasonable maximum (5 years = ~1825 days) to avoid API issues
                days_to_fetch = min(days_to_fetch, 1825)
            else:
                # Default: fetch last 365 days
                days_to_fetch = 365
            
            # Get historical data
            # For longer periods (>365 days), use get_symbol_history_with_interval which handles Yahoo Finance better
            # For shorter periods, use get_symbol_history (faster, simpler)
            if days_to_fetch > 365:
                # Use get_symbol_history_with_interval for longer periods (can use Yahoo Finance with 5y period)
                # Use prediction_horizon > 60 to get weekly/daily data
                prediction_horizon = min(days_to_fetch, 730)  # Cap at 730 for weekly
                try:
                    result = self.market_data_service.get_symbol_history_with_interval(symbol, prediction_horizon)
                    if isinstance(result, tuple):
                        historical_data, interval = result
                    else:
                        historical_data = result
                except Exception as e:
                    self.logger.warning(f"Error using get_symbol_history_with_interval for {symbol}, falling back to get_symbol_history: {e}")
                    historical_data = self.market_data_service.get_symbol_history(symbol, days=days_to_fetch)
            else:
                # Use get_symbol_history for shorter periods (returns list directly)
                historical_data = self.market_data_service.get_symbol_history(symbol, days=days_to_fetch)
            
            # Handle case where it might return tuple (data, interval) or None
            if historical_data is None:
                return None
            
            if isinstance(historical_data, tuple):
                historical_data = historical_data[0]
            
            if not isinstance(historical_data, list) or len(historical_data) == 0:
                return None
            
            # Find closest price to date (prefer exact match, then closest)
            target_date = date.date() if isinstance(date, datetime) else date
            closest_price = None
            min_diff = timedelta(days=365)
            exact_match = None
            
            for candle in historical_data:
                if not isinstance(candle, dict):
                    continue
                    
                candle_date_str = candle.get('timestamp', candle.get('date', ''))
                if not candle_date_str:
                    continue
                    
                try:
                    # Handle different date formats
                    if isinstance(candle_date_str, str):
                        if 'T' in candle_date_str:
                            candle_dt = datetime.fromisoformat(candle_date_str.replace('Z', '+00:00'))
                        else:
                            try:
                                candle_dt = datetime.strptime(candle_date_str, '%Y-%m-%d')
                            except ValueError:
                                continue
                    else:
                        continue
                    
                    candle_date = candle_dt.date()
                    price_value = candle.get('close', candle.get('price', 0))
                    
                    if not price_value:
                        continue
                    
                    try:
                        price = float(price_value)
                    except (ValueError, TypeError):
                        continue
                    
                    if price <= 0:
                        continue
                    
                    # Exact match
                    if candle_date == target_date:
                        exact_match = price
                        break
                    
                    # Find closest date
                    diff = abs(candle_date - target_date)
                    if diff < min_diff:
                        min_diff = diff
                        closest_price = price
                except Exception as e:
                    self.logger.debug(f"Error parsing candle data for {symbol}: {e}")
                    continue
            
            # Return exact match if found
            if exact_match is not None:
                return float(exact_match)
            
            # Use closest price if within 30 days
            if closest_price is not None:
                if min_diff <= timedelta(days=30):
                    self.logger.debug(f"Using closest price for {symbol} on {target_date} (diff: {min_diff.days} days)")
                    return float(closest_price)
                else:
                    self.logger.warning(f"No price found for {symbol} within 30 days of {target_date}")
            
            # Fallback: Use last available price from historical data
            # This ensures backtest can continue even if exact date not found
            last_candle = historical_data[-1] if historical_data else None
            if last_candle:
                price_value = last_candle.get('close', last_candle.get('price', 0))
                if price_value:
                    try:
                        fallback_price = float(price_value)
                        if fallback_price > 0:
                            self.logger.warning(f"No price found for {symbol} on {target_date}, using last available price")
                            return fallback_price
                    except (ValueError, TypeError):
                        pass
            
            self.logger.error(f"No price data available for {symbol} on {target_date}")
            return None
            
        except Exception as e:
            self.logger.warning(f"Error getting historical price for {symbol} on {date}: {e}")
            return None
    
    def _close_position(
        self,
        symbol: str,
        position: Dict,
        exit_price: float,
        exit_date: datetime,
        positions: Dict,
        trade_history: List,
        reason: str,
        transaction_cost: float = 0.0
    ) -> Tuple[float, float, float]:
        """
        Close a position and update trade history.
        
        Args:
            symbol: Symbol of the position to close
            position: Position dict with 'shares', 'entry_price', 'entry_date'
            exit_price: Price at which to close the position
            exit_date: Date of closing
            positions: Dict of open positions (will be modified - symbol removed)
            trade_history: List to append trade record to
            reason: Reason for closing the position
            transaction_cost: Transaction cost as decimal (e.g., 0.001 = 0.1%)
        
        Returns:
            Tuple of (cash_added, profit, transaction_cost_incurred)
        """
        # Extract position data
        shares = position.get('shares', 0)
        entry_price = position.get('entry_price', 0)
        entry_date = position.get('entry_date', '')
        
        if shares <= 0 or entry_price <= 0:
            self.logger.warning(f"Invalid position data for {symbol}: shares={shares}, entry_price={entry_price}")
            return 0.0, 0.0
        
        # Calculate exit value and profit
        exit_value = shares * exit_price
        profit = (exit_price - entry_price) * shares
        return_pct = ((exit_price - entry_price) / entry_price * 100) if entry_price > 0 else 0
        
        # Calculate transaction cost
        transaction_cost_amount = exit_value * transaction_cost if transaction_cost > 0 else 0.0
        cash_added = exit_value - transaction_cost_amount
        
        # Remove position from positions dict (if it exists)
        if symbol in positions:
            positions.pop(symbol)
        
        # Log the trade for debugging
        self.logger.debug(
            f"Closing position: {symbol} - Entry: ${entry_price:.2f}, Exit: ${exit_price:.2f}, "
            f"Shares: {shares:.4f}, Profit: ${profit:.2f}, Return: {return_pct:.2f}%"
        )
        
        # Record trade in history
        trade_history.append({
            'date': exit_date.strftime('%Y-%m-%d') if isinstance(exit_date, datetime) else exit_date,
            'action': 'sell',
            'symbol': symbol,
            'price': exit_price,
            'shares': shares,
            'value': exit_value,
            'return_pct': round(return_pct, 2),
            'profit': round(profit, 2),
            'reason': reason,
            'entry_price': entry_price,
            'entry_date': entry_date,
            'transaction_cost': round(transaction_cost_amount, 2)
        })
        
        return cash_added, profit, transaction_cost_amount
    
    def get_universe_symbols(self, index: str = 'SP500') -> List[str]:
        """
        Get list of symbols for a given index/universe.
        
        Args:
            index: Index name ('SP500' or 'RUSSELL2000')
            
        Returns:
            List of stock symbols
        """
        # Try to fetch from Wikipedia (most reliable free source)
        try:
            if index == 'SP500':
                import requests
                from bs4 import BeautifulSoup
                
                url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                response = requests.get(url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    table = soup.find('table', {'id': 'constituents'})
                    if table:
                        symbols = []
                        rows = table.find_all('tr')[1:]  # Skip header
                        for row in rows:
                            cells = row.find_all('td')
                            if cells:
                                symbol = cells[0].get_text(strip=True)
                                # Replace dots with hyphens for class shares (e.g., BRK.B -> BRK-B)
                                symbol = symbol.replace('.', '-')
                                symbols.append(symbol)
                        
                        if symbols:
                            self.logger.info(f"Fetched {len(symbols)} symbols from S&P 500 Wikipedia page")
                            return symbols
        except Exception as e:
            self.logger.warning(f"Error fetching {index} from Wikipedia: {e}. Using fallback list.")
        
        # Fallback: Use comprehensive list
        if index == 'SP500':
            # Fallback: Common S&P 500 stocks (top 100)
            return [
                'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'NVDA', 'META', 'TSLA', 'BRK-B',
                'V', 'JNJ', 'WMT', 'JPM', 'MA', 'PG', 'UNH', 'HD', 'DIS', 'PYPL',
                'BAC', 'VZ', 'ADBE', 'CMCSA', 'NFLX', 'NKE', 'MRK', 'PFE', 'T',
                'INTC', 'PEP', 'CSCO', 'TMO', 'AVGO', 'COST', 'ABT', 'ACN', 'CVX',
                'XOM', 'DHR', 'MDT', 'WFC', 'ABBV', 'ORCL', 'LLY', 'PM', 'NEE',
                'TXN', 'HON', 'UNP', 'UPS', 'IBM', 'BMY', 'AMGN', 'CI', 'SPGI',
                'RTX', 'DE', 'ADP', 'GS', 'CAT', 'AMAT', 'LMT', 'MU', 'BKNG',
                'C', 'AXP', 'MMC', 'CB', 'ADI', 'MCD', 'GE', 'ISRG', 'SYK',
                'EQIX', 'REGN', 'MCHP', 'ELV', 'CDNS', 'SNPS', 'ZTS', 'APH',
                'CL', 'FTNT', 'ROP', 'KLAC', 'WDAY', 'FANG', 'ODFL', 'CME',
                'AON', 'ICE', 'EW', 'ETN', 'ITW', 'PH', 'EMR', 'TT', 'APD'
            ]
        elif index == 'RUSSELL2000':
            # Russell 2000: Full implementation would require API access (e.g., FTSE Russell API)
            # For now, use a representative sample of smaller-cap stocks
            self.logger.info("Russell 2000: Using sample list (full implementation requires API access)")
            return [
                'AAL', 'AMD', 'ADSK', 'AKAM', 'ALGN', 'ALXN', 'AMAT', 'AMGN',
                'ANSS', 'APH', 'ATVI', 'AVGO', 'BBY', 'BIDU', 'BIIB',
                'BKNG', 'CDNS', 'CDW', 'CERN', 'CHTR', 'COST', 'CSX',
                'CTAS', 'CTSH', 'CTXS', 'DLTR', 'EA', 'EBAY', 'EXPD', 'FAST',
                'FISV', 'FOX', 'FOXA', 'GILD', 'HAS',
                'HSIC', 'IDXX', 'ILMN', 'INCY', 'INTU', 'ISRG', 'JBHT',
                'KLAC', 'LRCX', 'LULU', 'MAR', 'MCHP',
                'MDLZ', 'MELI', 'MNST', 'MXIM', 'NFLX', 'NTES',
                'NTAP', 'NXPI', 'ORLY', 'PAYX', 'PCAR', 'PYPL',
                'QCOM', 'REGN', 'ROST', 'SBUX', 'SGEN', 'SIRI', 'SNPS', 'SPLK',
                'SWKS', 'TCOM', 'TXN', 'ULTA', 'VRSK',
                'VRSN', 'VRTX', 'WDC', 'WDAY', 'WYNN', 'XEL', 'ZM'
            ]
        else:
            return []
    
    def rank_universe_by_ebit_ev(self, symbols: List[str], percentile: float = 0.2) -> List[Dict]:
        """
        Rank universe of symbols by EBIT/EV (Value metric).
        Returns bottom percentile (highest EBIT/EV = lowest valuation = best value).
        
        Args:
            symbols: List of symbols to rank
            percentile: Percentile to return (0.2 = bottom 20% = best value)
            
        Returns:
            List of dicts with symbol and EBIT/EV, sorted by EBIT/EV descending
        """
        ranked = []
        
        for symbol in symbols:
            try:
                financial_data = self.get_fundamental_data(symbol)
                if not financial_data:
                    continue
                
                magic_formula = self.calculate_magic_formula_metrics(symbol, financial_data=financial_data)
                ebit_ev = magic_formula.get('ebit_ev', 0)
                
                if ebit_ev > 0:  # Only include positive EBIT/EV
                    ranked.append({
                        'symbol': symbol,
                        'ebit_ev': ebit_ev,
                        'company_name': financial_data.get('company_name', symbol)
                    })
            except Exception as e:
                self.logger.debug(f"Error ranking {symbol} by EBIT/EV: {e}")
                continue
        
        # Sort by EBIT/EV descending (highest = best value)
        ranked.sort(key=lambda x: x['ebit_ev'], reverse=True)
        
        # Return bottom percentile
        num_to_return = max(1, int(len(ranked) * percentile))
        return ranked[:num_to_return]

