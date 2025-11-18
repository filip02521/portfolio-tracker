"""
Sector Analysis System for Portfolio Tracker
"""
import pandas as pd
from typing import Dict, List, Optional
import json
import os

class SectorAnalysis:
    """System analizy sektorowej portfolio"""
    
    def __init__(self, sectors_file='sector_mapping.json'):
        self.sectors_file = sectors_file
        self.sector_mapping = self.load_sector_mapping()
    
    def load_sector_mapping(self):
        """Load asset to sector mapping"""
        if os.path.exists(self.sectors_file):
            try:
                with open(self.sectors_file, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        
        # Default sector mapping
        default_mapping = {
            # Cryptocurrencies
            'BTC': 'Kryptowaluty',
            'ETH': 'Kryptowaluty',
            'SOL': 'Kryptowaluty',
            'ADA': 'Kryptowaluty',
            'DOT': 'Kryptowaluty',
            'LINK': 'Kryptowaluty',
            'UNI': 'Kryptowaluty',
            'AAVE': 'Kryptowaluty',
            'MATIC': 'Kryptowaluty',
            'AVAX': 'Kryptowaluty',
            'ATOM': 'Kryptowaluty',
            'NEAR': 'Kryptowaluty',
            'FTM': 'Kryptowaluty',
            'ALGO': 'Kryptowaluty',
            'VET': 'Kryptowaluty',
            'ICP': 'Kryptowaluty',
            'FIL': 'Kryptowaluty',
            'TRX': 'Kryptowaluty',
            'XRP': 'Kryptowaluty',
            'LTC': 'Kryptowaluty',
            'BCH': 'Kryptowaluty',
            'DOGE': 'Kryptowaluty',
            'SHIB': 'Kryptowaluty',
            'STRK': 'Kryptowaluty',
            'API3': 'Kryptowaluty',
            
            # Technology Stocks
            'AAPL': 'Technologia',
            'MSFT': 'Technologia',
            'GOOGL': 'Technologia',
            'GOOG': 'Technologia',
            'AMZN': 'Technologia',
            'META': 'Technologia',
            'TSLA': 'Technologia',
            'NVDA': 'Technologia',
            'NFLX': 'Technologia',
            'CRM': 'Technologia',
            'ADBE': 'Technologia',
            'INTC': 'Technologia',
            'AMD': 'Technologia',
            'ORCL': 'Technologia',
            'IBM': 'Technologia',
            'CSCO': 'Technologia',
            'QCOM': 'Technologia',
            'TXN': 'Technologia',
            'AVGO': 'Technologia',
            'NOW': 'Technologia',
            
            # Finance
            'JPM': 'Finanse',
            'BAC': 'Finanse',
            'WFC': 'Finanse',
            'GS': 'Finanse',
            'MS': 'Finanse',
            'C': 'Finanse',
            'AXP': 'Finanse',
            'V': 'Finanse',
            'MA': 'Finanse',
            'PYPL': 'Finanse',
            'SQ': 'Finanse',
            'COIN': 'Finanse',
            
            # Healthcare
            'JNJ': 'Zdrowie',
            'PFE': 'Zdrowie',
            'UNH': 'Zdrowie',
            'ABBV': 'Zdrowie',
            'MRK': 'Zdrowie',
            'TMO': 'Zdrowie',
            'ABT': 'Zdrowie',
            'DHR': 'Zdrowie',
            'BMY': 'Zdrowie',
            'AMGN': 'Zdrowie',
            
            # Consumer
            'PG': 'Konsumenckie',
            'KO': 'Konsumenckie',
            'PEP': 'Konsumenckie',
            'WMT': 'Konsumenckie',
            'HD': 'Konsumenckie',
            'MCD': 'Konsumenckie',
            'NKE': 'Konsumenckie',
            'SBUX': 'Konsumenckie',
            'DIS': 'Konsumenckie',
            'CMCSA': 'Konsumenckie',
            
            # Energy
            'XOM': 'Energetyka',
            'CVX': 'Energetyka',
            'COP': 'Energetyka',
            'EOG': 'Energetyka',
            'SLB': 'Energetyka',
            'KMI': 'Energetyka',
            
            # Industrial
            'BA': 'Przemysł',
            'CAT': 'Przemysł',
            'GE': 'Przemysł',
            'HON': 'Przemysł',
            'MMM': 'Przemysł',
            'RTX': 'Przemysł',
            
            # Materials
            'LIN': 'Surowce',
            'APD': 'Surowce',
            'ECL': 'Surowce',
            'SHW': 'Surowce',
            'DD': 'Surowce',
            
            # Utilities
            'NEE': 'Usługi Publiczne',
            'DUK': 'Usługi Publiczne',
            'SO': 'Usługi Publiczne',
            'AEP': 'Usługi Publiczne',
            'EXC': 'Usługi Publiczne',
            
            # Real Estate
            'AMT': 'Nieruchomości',
            'PLD': 'Nieruchomości',
            'CCI': 'Nieruchomości',
            'EQIX': 'Nieruchomości',
            'PSA': 'Nieruchomości',
            
            # Communication
            'VZ': 'Telekomunikacja',
            'T': 'Telekomunikacja',
            'TMUS': 'Telekomunikacja',
            'CHTR': 'Telekomunikacja',
            
            # ETFs
            'SPY': 'ETF',
            'QQQ': 'ETF',
            'IWM': 'ETF',
            'VTI': 'ETF',
            'VOO': 'ETF',
            'VEA': 'ETF',
            'VWO': 'ETF',
            'BND': 'ETF',
            'TLT': 'ETF',
            'GLD': 'ETF',
            'SLV': 'ETF',
            'USO': 'ETF',
            'XLF': 'ETF',
            'XLK': 'ETF',
            'XLE': 'ETF',
            'XLV': 'ETF',
            'XLI': 'ETF',
            'XLY': 'ETF',
            'XLP': 'ETF',
            'XLU': 'ETF',
            'XLB': 'ETF',
            'XLRE': 'ETF',
            'XLC': 'ETF',
            'XLU': 'ETF'
        }
        
        self.save_sector_mapping(default_mapping)
        return default_mapping
    
    def save_sector_mapping(self, mapping=None):
        """Save sector mapping to file"""
        if mapping is None:
            mapping = self.sector_mapping
        
        with open(self.sectors_file, 'w') as f:
            json.dump(mapping, f, indent=2)
    
    def get_asset_sector(self, asset_symbol: str) -> str:
        """Get sector for a given asset symbol"""
        return self.sector_mapping.get(asset_symbol.upper(), 'Inne')
    
    def analyze_portfolio_sectors(self, portfolios: List[Dict]) -> Dict:
        """Analyze portfolio by sectors"""
        sector_data = {}
        
        for portfolio in portfolios:
            exchange = portfolio['exchange']
            
            for balance in portfolio['balances']:
                asset = balance['asset']
                value_usdt = balance.get('value_usdt', 0)
                
                if value_usdt > 0:
                    sector = self.get_asset_sector(asset)
                    
                    if sector not in sector_data:
                        sector_data[sector] = {
                            'total_value': 0,
                            'percentage': 0,
                            'assets': {},
                            'exchanges': {}
                        }
                    
                    sector_data[sector]['total_value'] += value_usdt
                    
                    # Track assets in sector
                    if asset not in sector_data[sector]['assets']:
                        sector_data[sector]['assets'][asset] = 0
                    sector_data[sector]['assets'][asset] += value_usdt
                    
                    # Track exchanges in sector
                    if exchange not in sector_data[sector]['exchanges']:
                        sector_data[sector]['exchanges'][exchange] = 0
                    sector_data[sector]['exchanges'][exchange] += value_usdt
        
        # Calculate percentages
        total_value = sum(sector['total_value'] for sector in sector_data.values())
        
        for sector in sector_data.values():
            if total_value > 0:
                sector['percentage'] = (sector['total_value'] / total_value) * 100
        
        return sector_data
    
    def get_sector_recommendations(self, sector_data: Dict) -> List[str]:
        """Get recommendations based on sector analysis"""
        recommendations = []
        
        if not sector_data:
            return recommendations
        
        # Check for over-concentration
        max_sector_percentage = max(sector['percentage'] for sector in sector_data.values())
        
        if max_sector_percentage > 50:
            max_sector = max(sector_data.items(), key=lambda x: x[1]['percentage'])
            recommendations.append(f"⚠️ Wysoka koncentracja w sektorze '{max_sector[0]}' ({max_sector[1]['percentage']:.1f}%)")
            recommendations.append("Rozważ dywersyfikację do innych sektorów")
        
        # Check for crypto concentration
        crypto_percentage = sector_data.get('Kryptowaluty', {}).get('percentage', 0)
        if crypto_percentage > 30:
            recommendations.append(f"📈 Wysoka ekspozycja na kryptowaluty ({crypto_percentage:.1f}%)")
            recommendations.append("Rozważ dodanie tradycyjnych aktywów")
        elif crypto_percentage < 5:
            recommendations.append("💡 Niska ekspozycja na kryptowaluty")
            recommendations.append("Rozważ dodanie krypto do dywersyfikacji")
        
        # Check for technology concentration
        tech_percentage = sector_data.get('Technologia', {}).get('percentage', 0)
        if tech_percentage > 40:
            recommendations.append(f"💻 Wysoka koncentracja w technologii ({tech_percentage:.1f}%)")
            recommendations.append("Rozważ dodanie innych sektorów")
        
        # Check for diversification
        num_sectors = len(sector_data)
        if num_sectors < 3:
            recommendations.append("📊 Niska dywersyfikacja sektorowa")
            recommendations.append("Rozważ dodanie aktywów z różnych sektorów")
        elif num_sectors >= 5:
            recommendations.append("✅ Dobra dywersyfikacja sektorowa")
        
        # Check for missing sectors
        important_sectors = ['Technologia', 'Finanse', 'Zdrowie', 'Konsumenckie']
        missing_sectors = [sector for sector in important_sectors if sector not in sector_data]
        
        if missing_sectors:
            recommendations.append(f"🎯 Brakuje sektorów: {', '.join(missing_sectors)}")
            recommendations.append("Rozważ dodanie aktywów z tych sektorów")
        
        return recommendations
    
    def get_top_assets_by_sector(self, sector_data: Dict, top_n: int = 5) -> Dict[str, List]:
        """Get top assets in each sector"""
        top_assets = {}
        
        for sector, data in sector_data.items():
            assets = data['assets']
            sorted_assets = sorted(assets.items(), key=lambda x: x[1], reverse=True)
            top_assets[sector] = sorted_assets[:top_n]
        
        return top_assets
    
    def calculate_sector_risk_metrics(self, sector_data: Dict) -> Dict:
        """Calculate risk metrics for sectors"""
        if not sector_data:
            return {}
        
        percentages = [sector['percentage'] for sector in sector_data.values()]
        
        # Calculate concentration risk (Herfindahl-Hirschman Index)
        hhi = sum(p**2 for p in percentages) / 10000  # Normalize to 0-1
        
        # Calculate effective number of sectors
        effective_sectors = 1 / sum((p/100)**2 for p in percentages) if percentages else 0
        
        # Risk assessment
        if hhi > 0.25:
            risk_level = "Wysokie"
        elif hhi > 0.15:
            risk_level = "Średnie"
        else:
            risk_level = "Niskie"
        
        return {
            'hhi': hhi,
            'effective_sectors': effective_sectors,
            'risk_level': risk_level,
            'concentration_risk': hhi,
            'diversification_score': min(effective_sectors / 10, 1.0)  # Score 0-1
        }

# Example usage
if __name__ == "__main__":
    # Test sector analysis
    analyzer = SectorAnalysis()
    
    # Sample portfolio data
    sample_portfolios = [
        {
            'exchange': 'Binance',
            'balances': [
                {'asset': 'BTC', 'value_usdt': 5000},
                {'asset': 'ETH', 'value_usdt': 3000},
                {'asset': 'SOL', 'value_usdt': 2000}
            ]
        },
        {
            'exchange': 'XTB',
            'balances': [
                {'asset': 'AAPL', 'value_usdt': 4000},
                {'asset': 'MSFT', 'value_usdt': 3000},
                {'asset': 'GOOGL', 'value_usdt': 2000}
            ]
        }
    ]
    
    # Analyze sectors
    sector_data = analyzer.analyze_portfolio_sectors(sample_portfolios)
    
    print("Sector Analysis Results:")
    for sector, data in sector_data.items():
        print(f"\n{sector}:")
        print(f"  Value: ${data['total_value']:,.2f}")
        print(f"  Percentage: {data['percentage']:.2f}%")
        print(f"  Assets: {len(data['assets'])}")
    
    # Get recommendations
    recommendations = analyzer.get_sector_recommendations(sector_data)
    print(f"\nRecommendations:")
    for rec in recommendations:
        print(f"• {rec}")
    
    # Calculate risk metrics
    risk_metrics = analyzer.calculate_sector_risk_metrics(sector_data)
    print(f"\nRisk Metrics:")
    print(f"• HHI: {risk_metrics['hhi']:.3f}")
    print(f"• Effective Sectors: {risk_metrics['effective_sectors']:.1f}")
    print(f"• Risk Level: {risk_metrics['risk_level']}")
    print(f"• Diversification Score: {risk_metrics['diversification_score']:.2f}")
