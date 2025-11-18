#!/usr/bin/env python3
"""
Main application entry point for Portfolio Tracker
"""
import sys
from portfolio_tracker import PortfolioTracker
from config import Config

def main():
    """Main function"""
    print("\n" + "="*60)
    print("🚀 Portfolio Tracker - XTB, Binance, Bybit")
    print("="*60 + "\n")
    
    # Validate configuration
    missing = Config.validate()
    if missing:
        print(f"⚠️  Missing credentials for: {', '.join(missing)}")
        print("ℹ️  The application will continue with available exchanges.\n")
    
    # Initialize tracker
    try:
        tracker = PortfolioTracker()
        
        if not tracker.exchanges:
            print("\n❌ No exchanges configured. Please check your .env file.")
            print("💡 Tip: Copy env.example to .env and add your API credentials.")
            sys.exit(1)
        
        # Display portfolio
        tracker.display_portfolio()
        
        # Display detailed stats
        stats = tracker.get_detailed_stats()
        
        if stats['total_value'] > 0:
            print("\n📊 ALLOCATION BY EXCHANGE:")
            print("-" * 60)
            for exchange, data in stats['exchanges'].items():
                print(f"{exchange:15} ${data['value']:>15,.2f} ({data['percentage']:>5.2f}%)")
        
        print("\n✅ Portfolio tracking completed successfully!\n")
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Program interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

