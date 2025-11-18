"""
Test script to verify FIFO implementation
"""
from transaction_history import TransactionHistory

def test_fifo():
    """Test FIFO calculation with sample data"""
    
    # Create test transactions
    th = TransactionHistory('test_transactions.json')
    
    # Clear existing test data
    th.transactions = []
    
    # Add test transactions
    th.add_transaction("Test", "BTC", 1.0, 50000.0, "buy", "2024-01-01T00:00:00", 0.0)
    th.add_transaction("Test", "BTC", 1.0, 60000.0, "buy", "2024-01-02T00:00:00", 0.0)
    th.add_transaction("Test", "BTC", 1.0, 70000.0, "sell", "2024-01-03T00:00:00", 0.0)
    
    # Calculate PNL
    realized_pnl = th.get_total_realized_pnl()
    
    # Expected: Sell 1 BTC at 70k, first buy was at 50k, so profit = 20k
    expected_pnl = 20000.0
    
    print(f"Test FIFO calculation:")
    print(f"  Buy 1 BTC at $50,000")
    print(f"  Buy 1 BTC at $60,000") 
    print(f"  Sell 1 BTC at $70,000")
    print(f"  Expected PNL: ${expected_pnl:,.2f}")
    print(f"  Calculated PNL: ${realized_pnl:,.2f}")
    
    if abs(realized_pnl - expected_pnl) < 0.01:
        print("✅ FIFO test PASSED")
    else:
        print("❌ FIFO test FAILED")
    
    # Test with commission
    th.transactions = []
    th.add_transaction("Test", "ETH", 1.0, 3000.0, "buy", "2024-01-01T00:00:00", 10.0)
    th.add_transaction("Test", "ETH", 1.0, 4000.0, "sell", "2024-01-02T00:00:00", 15.0)
    
    realized_pnl_with_commission = th.get_total_realized_pnl()
    # Expected: Sell at 4000, buy at 3000, commission: 10+15=25, so profit = 1000-25 = 975
    expected_pnl_with_commission = 975.0
    
    print(f"\nTest FIFO with commission:")
    print(f"  Buy 1 ETH at $3,000 (commission $10)")
    print(f"  Sell 1 ETH at $4,000 (commission $15)")
    print(f"  Expected PNL: ${expected_pnl_with_commission:,.2f}")
    print(f"  Calculated PNL: ${realized_pnl_with_commission:,.2f}")
    
    if abs(realized_pnl_with_commission - expected_pnl_with_commission) < 0.01:
        print("✅ FIFO with commission test PASSED")
    else:
        print("❌ FIFO with commission test FAILED")

if __name__ == "__main__":
    test_fifo()
