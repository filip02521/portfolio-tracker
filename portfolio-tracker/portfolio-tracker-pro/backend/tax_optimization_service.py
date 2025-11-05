"""
Tax Optimization Service for Portfolio Tracker Pro
Provides tax calculations, tax-loss harvesting suggestions, and scenario planning
"""
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class TaxOptimizationService:
    """Service for tax optimization calculations and recommendations"""
    
    # Polish tax rates (2025)
    CAPITAL_GAINS_TAX_RATE = 0.19  # 19% for capital gains
    ANNUAL_FREE_AMOUNT = 85528  # PLN free amount per year (2025)
    
    def calculate_tax(self, realized_gains: float, realized_losses: float = 0, 
                     exchange_rate: float = 4.0) -> Dict:
        """
        Calculate tax on realized gains/losses
        
        Args:
            realized_gains: Total realized gains in USD
            realized_losses: Total realized losses in USD
            exchange_rate: USD to PLN exchange rate
            
        Returns:
            Tax calculation breakdown
        """
        # Convert to PLN
        gains_pln = realized_gains * exchange_rate
        losses_pln = realized_losses * exchange_rate
        
        # Net taxable amount
        net_taxable = gains_pln - losses_pln
        
        # Apply free amount (if applicable)
        taxable_after_free = max(0, net_taxable - self.ANNUAL_FREE_AMOUNT)
        
        # Calculate tax
        tax_amount = taxable_after_free * self.CAPITAL_GAINS_TAX_RATE
        
        # Effective tax rate
        effective_rate = (tax_amount / gains_pln * 100) if gains_pln > 0 else 0
        
        return {
            "realized_gains_usd": realized_gains,
            "realized_losses_usd": realized_losses,
            "realized_gains_pln": gains_pln,
            "realized_losses_pln": losses_pln,
            "net_taxable_pln": net_taxable,
            "free_amount_used": min(net_taxable, self.ANNUAL_FREE_AMOUNT),
            "taxable_amount_pln": taxable_after_free,
            "tax_amount_pln": tax_amount,
            "tax_amount_usd": tax_amount / exchange_rate,
            "effective_tax_rate": effective_rate,
            "tax_rate": self.CAPITAL_GAINS_TAX_RATE * 100
        }
    
    def suggest_tax_loss_harvesting(self, transactions: List[Dict], 
                                   current_year_gains: float,
                                   exchange_rate: float = 4.0) -> List[Dict]:
        """
        Suggest assets for tax-loss harvesting
        
        Args:
            transactions: List of transactions
            current_year_gains: Current year realized gains in USD
            exchange_rate: USD to PLN exchange rate
            
        Returns:
            List of suggested assets to sell for tax-loss harvesting
        """
        suggestions = []
        
        # Group transactions by asset
        asset_positions = {}
        
        for tx in transactions:
            asset = tx.get('asset', '')
            tx_type = tx.get('type', '').lower()
            amount = tx.get('amount', 0)
            price = tx.get('price_usd', 0)
            
            if asset not in asset_positions:
                asset_positions[asset] = {
                    'total_bought': 0,
                    'total_cost': 0,
                    'avg_cost': 0,
                    'current_amount': 0
                }
            
            if tx_type == 'buy':
                asset_positions[asset]['total_bought'] += amount
                asset_positions[asset]['total_cost'] += amount * price
            elif tx_type == 'sell':
                asset_positions[asset]['total_bought'] -= amount
        
        # Calculate unrealized losses
        # Note: This is simplified - we'd need current prices
        for asset, position in asset_positions.items():
            if position['total_bought'] > 0:
                avg_cost = position['total_cost'] / position['total_bought'] if position['total_bought'] > 0 else 0
                
                # Estimate current price (would need real-time data)
                # For now, we'll flag assets with potential losses based on recent sell prices
                
                # Find recent sell transactions to estimate current price
                recent_sells = [
                    tx for tx in transactions 
                    if tx.get('asset') == asset and tx.get('type', '').lower() == 'sell'
                ]
                
                if recent_sells:
                    # Use most recent sell price as estimate
                    estimated_price = recent_sells[-1].get('price_usd', 0)
                    
                    if estimated_price < avg_cost and position['total_bought'] > 0:
                        # Potential loss
                        potential_loss = (avg_cost - estimated_price) * position['total_bought']
                        potential_loss_pln = potential_loss * exchange_rate
                        
                        # Tax savings from harvesting this loss
                        tax_savings = potential_loss_pln * self.CAPITAL_GAINS_TAX_RATE
                        
                        if tax_savings > 0:
                            suggestions.append({
                                "asset": asset,
                                "amount": position['total_bought'],
                                "avg_cost": avg_cost,
                                "current_price_estimate": estimated_price,
                                "potential_loss_usd": potential_loss,
                                "potential_loss_pln": potential_loss_pln,
                                "tax_savings_pln": tax_savings,
                                "tax_savings_usd": tax_savings / exchange_rate,
                                "priority": "high" if tax_savings > 1000 else "medium"
                            })
        
        # Sort by tax savings
        suggestions.sort(key=lambda x: x['tax_savings_pln'], reverse=True)
        
        return suggestions[:5]  # Top 5 suggestions
    
    def calculate_scenario(self, current_gains: float, current_losses: float,
                          additional_losses: float, exchange_rate: float = 4.0) -> Dict:
        """
        Calculate tax scenario with additional losses
        
        Args:
            current_gains: Current realized gains in USD
            current_losses: Current realized losses in USD
            additional_losses: Additional losses to realize in USD
            exchange_rate: USD to PLN exchange rate
            
        Returns:
            Scenario comparison
        """
        # Current scenario
        current_tax = self.calculate_tax(current_gains, current_losses, exchange_rate)
        
        # Scenario with additional losses
        new_losses = current_losses + additional_losses
        new_tax = self.calculate_tax(current_gains, new_losses, exchange_rate)
        
        tax_savings = current_tax['tax_amount_pln'] - new_tax['tax_amount_pln']
        
        return {
            "current_tax": current_tax,
            "proposed_tax": new_tax,
            "tax_savings_pln": tax_savings,
            "tax_savings_usd": tax_savings / exchange_rate,
            "savings_percentage": (tax_savings / current_tax['tax_amount_pln'] * 100) if current_tax['tax_amount_pln'] > 0 else 0
        }
    
    def get_tax_deadline_info(self) -> Dict:
        """Get information about tax deadlines"""
        now = datetime.now()
        year_end = datetime(now.year, 12, 31)
        days_until_year_end = (year_end - now).days
        
        # PIT deadline (usually end of April next year)
        pit_deadline = datetime(now.year + 1, 4, 30)
        days_until_pit = (pit_deadline - now).days
        
        return {
            "current_year": now.year,
            "days_until_year_end": days_until_year_end,
            "pit_deadline": pit_deadline.isoformat(),
            "days_until_pit_deadline": days_until_pit,
            "urgent": days_until_year_end < 30,
            "warning": days_until_year_end < 60
        }


