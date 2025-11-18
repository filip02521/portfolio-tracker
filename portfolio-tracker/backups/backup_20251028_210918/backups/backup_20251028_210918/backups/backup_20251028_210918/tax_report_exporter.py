"""
CSV Export functionality for tax reports
"""
import csv
import json
from datetime import datetime
from typing import List, Dict
import pandas as pd

class TaxReportExporter:
    """Export transactions to CSV for tax purposes"""
    
    def __init__(self, transaction_history):
        self.th = transaction_history
    
    def export_transactions_csv(self, filename: str = None, year: int = None):
        """Export all transactions to CSV"""
        if filename is None:
            filename = f"transactions_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        transactions = self.th.get_all_transactions()
        
        # Filter by year if specified
        if year:
            transactions = [t for t in transactions if t['date'][:4] == str(year)]
        
        # Prepare CSV data
        csv_data = []
        for tx in transactions:
            csv_data.append({
                'ID': tx['id'],
                'Data': tx['date'][:10],
                'Giełda': tx['exchange'],
                'Aktywo': tx['asset'],
                'Typ': 'Kupno' if tx['type'] == 'buy' else 'Sprzedaż',
                'Ilość': tx['amount'],
                'Cena USD': tx['price_usd'],
                'Wartość USD': tx['value_usd'],
                'Kurs USD/PLN': tx.get('exchange_rate_usd_pln', ''),
                'Wartość PLN': tx.get('value_pln', ''),
                'Prowizja USD': tx.get('commission', 0.0),
                'Prowizja PLN': tx.get('commission', 0.0) * tx.get('exchange_rate_usd_pln', 0) if tx.get('exchange_rate_usd_pln') else '',
                'Waluta prowizji': tx.get('commission_currency', 'USD')
            })
        
        # Write CSV
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = csv_data[0].keys() if csv_data else []
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(csv_data)
        
        print(f"✅ Exported {len(csv_data)} transactions to {filename}")
        return filename
    
    def export_tax_report_csv(self, year: int, filename: str = None):
        """Export tax report for specific year"""
        if filename is None:
            filename = f"tax_report_{year}.csv"
        
        # Get transactions for the year
        transactions = [t for t in self.th.get_all_transactions() if t['date'][:4] == str(year)]
        
        if not transactions:
            print(f"No transactions found for year {year}")
            return None
        
        # Group by asset for FIFO calculation
        assets = {}
        for t in transactions:
            key = (t['exchange'], t['asset'])
            if key not in assets:
                assets[key] = {'buys': [], 'sells': []}
            
            if t['type'] == 'buy':
                assets[key]['buys'].append(t)
            else:
                assets[key]['sells'].append(t)
        
        # Calculate realized PNL per asset
        tax_data = []
        total_realized_pnl = 0
        
        for (exchange, asset), data in assets.items():
            buys = sorted(data['buys'], key=lambda x: x['date'])
            sells = sorted(data['sells'], key=lambda x: x['date'])
            
            if not sells:
                continue
            
            # FIFO calculation for this asset
            fifo_queue = []
            for buy in buys:
                fifo_queue.append({
                    'amount': buy['amount'],
                    'value_usd': buy['value_usd'],
                    'commission': buy.get('commission', 0.0),
                    'date': buy['date']
                })
            
            asset_realized_pnl = 0
            total_proceeds = 0
            total_cost = 0
            total_commission = 0
            
            for sell in sells:
                remaining_sell = sell['amount']
                sell_proceeds = sell['value_usd']
                sell_commission = sell.get('commission', 0.0)
                
                while remaining_sell > 0 and fifo_queue:
                    buy_lot = fifo_queue[0]
                    
                    if buy_lot['amount'] <= remaining_sell:
                        used_amount = buy_lot['amount']
                        cost_basis = buy_lot['value_usd']
                        cost_commission = buy_lot['commission']
                        
                        proceeds_portion = (used_amount / sell['amount']) * sell_proceeds
                        commission_portion = (used_amount / sell['amount']) * sell_commission
                        
                        realized_pnl = proceeds_portion - cost_basis - cost_commission - commission_portion
                        asset_realized_pnl += realized_pnl
                        
                        total_proceeds += proceeds_portion
                        total_cost += cost_basis
                        total_commission += cost_commission + commission_portion
                        
                        remaining_sell -= used_amount
                        fifo_queue.pop(0)
                    else:
                        used_amount = remaining_sell
                        cost_basis = (used_amount / buy_lot['amount']) * buy_lot['value_usd']
                        cost_commission = (used_amount / buy_lot['amount']) * buy_lot['commission']
                        
                        proceeds_portion = (used_amount / sell['amount']) * sell_proceeds
                        commission_portion = (used_amount / sell['amount']) * sell_commission
                        
                        realized_pnl = proceeds_portion - cost_basis - cost_commission - commission_portion
                        asset_realized_pnl += realized_pnl
                        
                        total_proceeds += proceeds_portion
                        total_cost += cost_basis
                        total_commission += cost_commission + commission_portion
                        
                        buy_lot['amount'] -= used_amount
                        buy_lot['value_usd'] -= cost_basis
                        buy_lot['commission'] -= cost_commission
                        
                        remaining_sell = 0
            
            if asset_realized_pnl != 0:
                tax_data.append({
                    'Giełda': exchange,
                    'Aktywo': asset,
                    'Przychód ze sprzedaży (USD)': total_proceeds,
                    'Koszt nabycia (USD)': total_cost,
                    'Prowizje (USD)': total_commission,
                    'Zysk/Strata (USD)': asset_realized_pnl,
                    'Podatek 19% (USD)': asset_realized_pnl * 0.19 if asset_realized_pnl > 0 else 0
                })
                total_realized_pnl += asset_realized_pnl
        
        # Add summary row
        tax_data.append({
            'Giełda': 'SUMA',
            'Aktywo': 'WSZYSTKIE',
            'Przychód ze sprzedaży (USD)': sum(row['Przychód ze sprzedaży (USD)'] for row in tax_data[:-1]),
            'Koszt nabycia (USD)': sum(row['Koszt nabycia (USD)'] for row in tax_data[:-1]),
            'Prowizje (USD)': sum(row['Prowizje (USD)'] for row in tax_data[:-1]),
            'Zysk/Strata (USD)': total_realized_pnl,
            'Podatek 19% (USD)': total_realized_pnl * 0.19 if total_realized_pnl > 0 else 0
        })
        
        # Write CSV
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = tax_data[0].keys() if tax_data else []
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(tax_data)
        
        print(f"✅ Tax report for {year} exported to {filename}")
        print(f"   Total realized PNL: ${total_realized_pnl:,.2f}")
        print(f"   Tax due (19%): ${total_realized_pnl * 0.19:,.2f}" if total_realized_pnl > 0 else "   No tax due")
        
        return filename

# Example usage
if __name__ == "__main__":
    from transaction_history import TransactionHistory
    
    th = TransactionHistory()
    exporter = TaxReportExporter(th)
    
    # Export all transactions
    exporter.export_transactions_csv()
    
    # Export tax report for 2024
    exporter.export_tax_report_csv(2024)
