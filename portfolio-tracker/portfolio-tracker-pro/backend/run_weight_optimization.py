#!/usr/bin/env python3
"""
Run weight optimization backtests for all configurations.

Usage:
    python run_weight_optimization.py [--period DAYS] [--thresholds THRESHOLDS] [--verbose] [--debug]

Options:
    --period DAYS: Number of days for backtest (default: 730 = 2 years)
    --thresholds THRESHOLDS: Comma-separated list of signal thresholds (default: "5.0,7.5,10.0,20.0,30.0,40.0,50.0")
    --verbose: Enable verbose logging
    --debug: Enable debug mode (export intermediate results to JSON)

This script will:
1. Load all weight configurations from weight_configs.json
2. Prefetch all historical data
3. Run backtests for each configuration
4. Analyze results and save to weight_optimization_results.json
"""
import sys
import os
import argparse
from datetime import datetime, timedelta
import logging

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from ai_weight_optimizer import (
    load_weight_configs,
    save_weight_configs,
    create_default_configurations,
    backtest_weight_configuration,
    analyze_backtest_results,
    save_backtest_results
)
from ai_service import AIService
from market_data_service import MarketDataService

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main function to run weight optimization"""
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Run weight optimization backtests')
    parser.add_argument('--period', type=int, default=730, help='Number of days for backtest (default: 730 = 2 years)')
    parser.add_argument('--thresholds', type=str, default='5.0,7.5,10.0,20.0,30.0,40.0,50.0', 
                       help='Comma-separated list of signal thresholds (default: "5.0,7.5,10.0,20.0,30.0,40.0,50.0")')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode (export intermediate results)')
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose or args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)
    
    # Load or create configurations
    logger.info("Loading weight configurations...")
    configs = load_weight_configs()
    
    if not configs:
        logger.info("No configs found, creating defaults...")
        configs = create_default_configurations()
        save_weight_configs(configs)
    
    logger.info(f"Found {len(configs)} configurations to test")
    
    # Initialize services
    logger.info("Initializing services...")
    market_data_service = MarketDataService()
    ai_service = AIService(market_data_service=market_data_service)
    
    # Backtest parameters
    end_date = datetime.now()
    start_date = end_date - timedelta(days=args.period)
    
    # Parse thresholds
    signal_thresholds = [float(t.strip()) for t in args.thresholds.split(',')]
    
    symbols = ['BTC', 'ETH', 'SOL', 'AAPL', 'MSFT', 'TSLA']
    initial_capital = 10000.0
    strategy = "follow_ai"
    
    # Prefetch all historical data before backtesting
    logger.info(f"\n{'='*60}")
    logger.info("Prefetching historical data for all symbols...")
    logger.info(f"{'='*60}")
    
    prefetch_start = datetime.now()
    for symbol in symbols:
        try:
            logger.info(f"Prefetching data for {symbol}...")
            # Use prediction_horizon > 60 to get weekly data for long-term backtests
            data, interval = market_data_service.get_symbol_history_with_interval(symbol, 90)
            if data:
                logger.info(f"  ✅ {symbol}: {len(data)} data points ({interval})")
            else:
                logger.warning(f"  ⚠️  {symbol}: No data available")
        except Exception as e:
            logger.error(f"  ❌ {symbol}: Error prefetching data - {e}")
    
    prefetch_duration = (datetime.now() - prefetch_start).total_seconds()
    logger.info(f"Prefetch completed in {prefetch_duration:.1f} seconds")
    logger.info(f"{'='*60}\n")
    
    logger.info(f"Backtest parameters:")
    logger.info(f"  Period: {args.period} days ({args.period // 365} years)")
    logger.info(f"  Start date: {start_date.strftime('%Y-%m-%d')}")
    logger.info(f"  End date: {end_date.strftime('%Y-%m-%d')}")
    logger.info(f"  Symbols: {symbols}")
    logger.info(f"  Signal thresholds: {signal_thresholds}")
    logger.info(f"  Initial capital: ${initial_capital:,.2f}")
    logger.info(f"  Strategy: {strategy}")
    logger.info(f"  Debug mode: {args.debug}")
    logger.info(f"  Verbose: {args.verbose}")
    
    # Run backtests for each configuration
    all_results = []
    
    for i, config in enumerate(configs, 1):
        logger.info(f"\n{'='*60}")
        logger.info(f"Testing configuration {i}/{len(configs)}: {config.name}")
        logger.info(f"Description: {config.description}")
        logger.info(f"{'='*60}")
        
        try:
            result = backtest_weight_configuration(
                config=config,
                ai_service=ai_service,
                symbols=symbols,
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d'),
                initial_capital=initial_capital,
                strategy=strategy,
                signal_thresholds=signal_thresholds
            )
            
            all_results.append(result)
            
            # Log summary for this config
            threshold_results = result.get('threshold_results', [])
            if threshold_results:
                logger.info(f"Results for {config.name}:")
                for tr in threshold_results:
                    if 'error' not in tr:
                        logger.info(
                            f"  Threshold {tr['signal_threshold']}: "
                            f"Return={tr.get('total_return', 0)*100:.2f}%, "
                            f"Sharpe={tr.get('sharpe_ratio', 0):.2f}, "
                            f"Win Rate={tr.get('win_rate', 0)*100:.1f}%"
                        )
                    else:
                        logger.warning(f"  Threshold {tr['signal_threshold']}: ERROR - {tr.get('error')}")
        except Exception as e:
            logger.error(f"Error testing configuration {config.name}: {e}", exc_info=True)
            all_results.append({
                "config_name": config.name,
                "error": str(e)
            })
    
    # Save all results
    logger.info(f"\n{'='*60}")
    logger.info("Saving results...")
    save_backtest_results(all_results)
    
    # Analyze results
    logger.info("Analyzing results...")
    analysis = analyze_backtest_results(all_results)
    
    # Print analysis summary
    logger.info(f"\n{'='*60}")
    logger.info("BACKTEST ANALYSIS SUMMARY")
    logger.info(f"{'='*60}")
    
    if analysis.get('configs_ranked'):
        logger.info("\nRankings (by composite score):")
        for i, config_summary in enumerate(analysis['configs_ranked'][:5], 1):
            logger.info(
                f"{i}. {config_summary['config_name']} (threshold={config_summary['threshold']}): "
                f"Sharpe={config_summary['sharpe_ratio']:.2f}, "
                f"Win Rate={config_summary['win_rate']*100:.1f}%, "
                f"Return={config_summary['total_return']*100:.2f}%, "
                f"Score={config_summary['composite_score']:.2f}"
            )
        
        if analysis.get('best_overall'):
            best = analysis['best_overall']
            logger.info(f"\n🏆 BEST OVERALL: {best['config_name']}")
            logger.info(f"   Threshold: {best['threshold']}")
            logger.info(f"   Sharpe Ratio: {best['sharpe_ratio']:.2f}")
            logger.info(f"   Win Rate: {best['win_rate']*100:.1f}%")
            logger.info(f"   Total Return: {best['total_return']*100:.2f}%")
            logger.info(f"   CAGR: {best['cagr']*100:.2f}%")
            logger.info(f"   Max Drawdown: {best['max_drawdown']*100:.2f}%")
    else:
        logger.warning("No successful backtest results to analyze")
    
    logger.info(f"\n{'='*60}")
    logger.info("Weight optimization complete!")
    logger.info(f"Results saved to: weight_optimization_results.json")
    logger.info(f"{'='*60}")


if __name__ == "__main__":
    main()
