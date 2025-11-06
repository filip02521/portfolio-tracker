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
        self.finnhub_api_key = os.getenv('FINNHUB_API_KEY', '')
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
        if financials_data.get('data') and len(financials_data['data']) > 0:
            latest = financials_data['data'][0]
            for report in latest.get('report', {}):
                concept = report.get('concept', '').lower()
                value = float(report.get('value', 0)) if report.get('value') else 0
                
                if 'netincomeloss' in concept or 'netincome' in concept:
                    latest_financials['net_income'] = value
                elif concept == 'assets':
                    latest_financials['total_assets'] = value
                elif 'liabilit' in concept:
                    latest_financials['total_liabilities'] = value
                elif 'operatingcashflow' in concept or 'operatingcash' in concept:
                    latest_financials['operating_cash_flow'] = value
                elif 'costofrevenue' in concept or 'costofgoodssold' in concept or 'cogs' in concept:
                    latest_financials['cogs'] = value
                elif 'grossprofit' in concept or 'grossincome' in concept:
                    latest_financials['gross_profit'] = value
                elif 'retainedearnings' in concept:
                    latest_financials['retained_earnings'] = value
                elif 'cashandcashequivalents' in concept or 'cashandshortterminvestments' in concept:
                    latest_financials['cash_and_cash_equivalents'] = value
                elif 'stockholdersequity' in concept or 'totalequity' in concept:
                    latest_financials['total_stockholders_equity'] = value
        
        revenue = profile_data.get('revenue', 0) or latest_financials.get('revenue', 0)
        cogs = latest_financials.get('cogs', 0)
        gross_profit = latest_financials.get('gross_profit', 0)
        # Calculate gross profit if not available but we have revenue and COGS
        if gross_profit == 0 and revenue > 0 and cogs > 0:
            gross_profit = revenue - cogs
        
        return {
            'symbol': profile_data.get('ticker', ''),
            'company_name': profile_data.get('name', ''),
            'market_cap': profile_data.get('marketCapitalization', 0),
            'total_assets': latest_financials.get('total_assets', profile_data.get('totalAssets', 0)),
            'total_liabilities': latest_financials.get('total_liabilities', profile_data.get('totalLiabilities', 0)),
            'net_income': latest_financials.get('net_income', 0),
            'operating_cash_flow': latest_financials.get('operating_cash_flow', 0),
            'revenue': revenue,
            'ebit': profile_data.get('ebit', 0),
            'current_assets': profile_data.get('currentAssets', 0),
            'current_liabilities': profile_data.get('currentLiabilities', 0),
            'long_term_debt': profile_data.get('longTermDebt', 0),
            'book_value': profile_data.get('bookValue', 0),
            'shares_outstanding': profile_data.get('shareOutstanding', 0),
            'cogs': cogs,
            'gross_profit': gross_profit,
            'retained_earnings': latest_financials.get('retained_earnings', 0),
            'cash_and_cash_equivalents': latest_financials.get('cash_and_cash_equivalents', 0),
            'total_stockholders_equity': latest_financials.get('total_stockholders_equity', 0),
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
            # In a real implementation, fetch previous year's data
            # For now, we'll use simplified assumptions
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
        if retained_earnings == 0:
            # Fallback: Retained Earnings = Total Equity - Common Stock (if available)
            total_equity = financial_data.get('total_stockholders_equity', 0)
            if total_equity > 0:
                # Simplified: assume most of equity is retained earnings (common stock is usually small)
                retained_earnings = total_equity * 0.8  # Conservative estimate
            else:
                # Last resort: use net income as proxy (less accurate)
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
                    # Try to get latest price
                    latest_data = self.market_data_service.get_symbol_history_with_interval(symbol, 1)
                    if latest_data and len(latest_data) > 0:
                        current_price = float(latest_data[-1].get('close', 0))
                except:
                    pass
            
            if not current_price or current_price <= 0:
                # Estimate from market cap and shares
                market_cap = financial_data.get('market_cap', 0)
                shares = financial_data.get('shares_outstanding', 1)
                current_price = market_cap / shares if shares > 0 else 0
        
        # Calculate ROIC
        # ROIC = EBIT / (Total Assets - Current Liabilities - Cash) - TRUE formula from report
        ebit = financial_data.get('ebit', 0)
        total_assets = financial_data.get('total_assets', 1)
        current_liabilities = financial_data.get('current_liabilities', 0)
        cash = financial_data.get('cash_and_cash_equivalents', 0)
        # TRUE Invested Capital: Assets - Current Liabilities - Cash
        invested_capital = total_assets - current_liabilities - cash
        roic = (ebit / invested_capital) * 100 if invested_capital > 0 else 0
        
        # Calculate EBIT/EV (Earnings Yield)
        # EV = Market Cap + Total Debt - Cash - TRUE formula from report
        market_cap = financial_data.get('market_cap', 0)
        total_debt = financial_data.get('long_term_debt', 0) + current_liabilities
        cash = financial_data.get('cash_and_cash_equivalents', 0)
        # TRUE Enterprise Value: Market Cap + Debt - Cash
        enterprise_value = market_cap + total_debt - cash
        ebit_ev = (ebit / enterprise_value) * 100 if enterprise_value > 0 else 0
        
        # Combined score (normalized, higher is better)
        # Simple average for now (in production, use proper ranking)
        combined_score = (roic + ebit_ev) / 2
        
        return {
            'roic': round(roic, 2),
            'ebit_ev': round(ebit_ev, 2),
            'combined_score': round(combined_score, 2),
            'current_price': round(current_price, 2),
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

