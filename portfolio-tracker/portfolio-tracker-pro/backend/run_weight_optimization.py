#!/usr/bin/env python3
"""
Run weight optimization backtests for all configurations.

Usage:
    python run_weight_optimization.py

This script will:
1. Load all weight configurations from weight_configs.json
2. Run backtests for each configuration
3. Analyze results and save to weight_optimization_results.json
"""
import sys
import os
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
    start_date = end_date - timedelta(days=180)  # Last 180 days
    
    symbols = ['BTC', 'ETH', 'SOL', 'AAPL', 'MSFT', 'TSLA']
    signal_thresholds = [10.0, 20.0, 30.0]
    initial_capital = 10000.0
    strategy = "follow_ai"
    
    logger.info(f"Backtest parameters:")
    logger.info(f"  Start date: {start_date.strftime('%Y-%m-%d')}")
    logger.info(f"  End date: {end_date.strftime('%Y-%m-%d')}")
    logger.info(f"  Symbols: {symbols}")
    logger.info(f"  Signal thresholds: {signal_thresholds}")
    logger.info(f"  Initial capital: ${initial_capital:,.2f}")
    logger.info(f"  Strategy: {strategy}")
    
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
