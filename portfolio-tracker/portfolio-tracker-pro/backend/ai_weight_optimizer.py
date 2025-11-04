"""
AI Weight Optimizer - Framework for testing different indicator weight configurations
"""
import json
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@dataclass
class WeightConfiguration:
    """Configuration of weights for all technical indicators"""
    
    # Momentum/Oscillatory Indicators
    rsi_weight: float = 15.0
    stochastic_oversold_weight: float = 8.0
    stochastic_overbought_weight: float = 8.0
    stochastic_crossover_weight: float = 6.0
    williams_r_weight: float = 4.0
    mfi_weight: float = 7.0
    cci_threshold: float = 150.0  # Threshold for CCI signals
    cci_weight: float = 8.0
    
    # Trend Indicators
    macd_crossover_weight: float = 20.0
    macd_trend_weight: float = 5.0  # Only used if no crossover
    ma50_weight: float = 5.0
    ma200_weight: float = 8.0
    golden_cross_weight: float = 10.0
    adx_weight: float = 8.0
    
    # Volatility Indicators
    bollinger_weight: float = 12.0
    donchian_weight: float = 10.0
    
    # Volume Indicators
    obv_weight: float = 5.0
    cmf_weight: float = 7.0
    vwap_weight: float = 6.0
    volume_roc_weight: float = 4.0
    
    # Other Indicators
    momentum_weight: float = 5.0
    support_resistance_weight: float = 8.0
    volume_profile_weight: float = 8.0
    chart_pattern_weight: float = 8.0  # Base weight for chart patterns
    candlestick_pattern_weight: float = 10.0
    correlation_weight: float = 3.0
    
    # Settings
    name: str = "default"
    description: str = ""
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'WeightConfiguration':
        """Create from dictionary"""
        return cls(**data)


def load_weight_configs(config_file: str = "weight_configs.json") -> List[WeightConfiguration]:
    """Load weight configurations from JSON file"""
    config_path = os.path.join(os.path.dirname(__file__), config_file)
    
    if not os.path.exists(config_path):
        logger.warning(f"Config file {config_path} not found, creating default")
        default_configs = create_default_configurations()
        save_weight_configs(default_configs, config_file)
        return default_configs
    
    try:
        with open(config_path, 'r') as f:
            configs_data = json.load(f)
        
        return [WeightConfiguration.from_dict(config_data) for config_data in configs_data]
    except Exception as e:
        logger.error(f"Error loading configs: {e}")
        return create_default_configurations()


def save_weight_configs(configs: List[WeightConfiguration], config_file: str = "weight_configs.json"):
    """Save weight configurations to JSON file"""
    config_path = os.path.join(os.path.dirname(__file__), config_file)
    
    try:
        configs_data = [config.to_dict() for config in configs]
        with open(config_path, 'w') as f:
            json.dump(configs_data, f, indent=2)
        logger.info(f"Saved {len(configs)} configurations to {config_path}")
    except Exception as e:
        logger.error(f"Error saving configs: {e}")


def create_default_configurations() -> List[WeightConfiguration]:
    """Create default weight configurations for testing"""
    
    configs = []
    
    # 1. Base configuration (current weights)
    configs.append(WeightConfiguration(
        name="base",
        description="Current weights as baseline"
    ))
    
    # 2. Without double-counting (per ANALYSIS_BEARISH_BULLISH.md)
    configs.append(WeightConfiguration(
        name="no_double_counting",
        description="Fixed double-counting: MACD crossover excludes trend, Golden Cross excludes MA weights",
        macd_crossover_weight=20.0,
        macd_trend_weight=5.0,  # Only when no crossover
        ma50_weight=5.0,
        ma200_weight=8.0,
        golden_cross_weight=10.0,  # When active, excludes MA50/MA200
        williams_r_weight=4.0,  # Reduced from 6
        cci_threshold=150.0,
        cci_weight=8.0
    ))
    
    # 3. Momentum-focused
    configs.append(WeightConfiguration(
        name="momentum_focused",
        description="Higher weights for momentum/oscillatory indicators",
        rsi_weight=20.0,  # Increased from 15
        stochastic_oversold_weight=10.0,  # Increased from 8
        stochastic_overbought_weight=10.0,
        stochastic_crossover_weight=8.0,  # Increased from 6
        williams_r_weight=6.0,
        mfi_weight=10.0,  # Increased from 7
        cci_weight=10.0,  # Increased from 8
        macd_crossover_weight=15.0,  # Reduced
        ma50_weight=3.0,  # Reduced
        ma200_weight=5.0,  # Reduced
        golden_cross_weight=5.0,  # Reduced
        adx_weight=5.0  # Reduced
    ))
    
    # 4. Trend-focused
    configs.append(WeightConfiguration(
        name="trend_focused",
        description="Higher weights for trend indicators",
        rsi_weight=10.0,  # Reduced
        stochastic_oversold_weight=5.0,  # Reduced
        stochastic_overbought_weight=5.0,
        mfi_weight=5.0,  # Reduced
        macd_crossover_weight=25.0,  # Increased from 20
        macd_trend_weight=8.0,  # Increased from 5
        ma50_weight=8.0,  # Increased from 5
        ma200_weight=12.0,  # Increased from 8
        golden_cross_weight=15.0,  # Increased from 10
        adx_weight=12.0  # Increased from 8
    ))
    
    # 5. Volume-focused
    configs.append(WeightConfiguration(
        name="volume_focused",
        description="Higher weights for volume indicators",
        obv_weight=10.0,  # Increased from 5
        cmf_weight=12.0,  # Increased from 7
        vwap_weight=10.0,  # Increased from 6
        volume_roc_weight=8.0,  # Increased from 4
        rsi_weight=12.0,  # Reduced
        macd_crossover_weight=15.0,  # Reduced
        ma50_weight=3.0,  # Reduced
        ma200_weight=5.0  # Reduced
    ))
    
    # 6. Conservative (higher thresholds, lower weights)
    configs.append(WeightConfiguration(
        name="conservative",
        description="Higher thresholds, lower weights for fewer but stronger signals",
        rsi_weight=12.0,  # Slightly reduced
        stochastic_oversold_weight=6.0,  # Reduced
        stochastic_overbought_weight=6.0,
        cci_threshold=200.0,  # Higher threshold
        cci_weight=6.0,  # Reduced
        macd_crossover_weight=18.0,  # Slightly reduced
        ma50_weight=4.0,
        ma200_weight=6.0,
        golden_cross_weight=8.0,
        bollinger_weight=10.0  # Reduced
    ))
    
    # 7. Aggressive (lower thresholds, higher weights)
    configs.append(WeightConfiguration(
        name="aggressive",
        description="Lower thresholds, higher weights for more signals",
        rsi_weight=18.0,  # Increased
        stochastic_oversold_weight=10.0,  # Increased
        stochastic_overbought_weight=10.0,
        stochastic_crossover_weight=8.0,
        cci_threshold=120.0,  # Lower threshold
        cci_weight=10.0,  # Increased
        macd_crossover_weight=22.0,  # Increased
        macd_trend_weight=7.0,  # Increased
        ma50_weight=7.0,  # Increased
        ma200_weight=10.0,  # Increased
        golden_cross_weight=12.0,  # Increased
        bollinger_weight=14.0  # Increased
    ))
    
    return configs


def backtest_weight_configuration(
    config: WeightConfiguration,
    ai_service: Any,  # AIService instance
    symbols: List[str],
    start_date: str,
    end_date: str,
    initial_capital: float = 10000.0,
    strategy: str = "follow_ai",
    signal_thresholds: List[float] = [10.0, 20.0, 30.0]
) -> Dict[str, Any]:
    """
    Backtest a weight configuration.
    
    Args:
        config: WeightConfiguration to test
        ai_service: AIService instance with modified weights
        symbols: List of symbols to test
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        initial_capital: Initial capital
        strategy: Strategy name ('follow_ai', etc.)
        signal_thresholds: List of signal thresholds to test
    
    Returns:
        Dictionary with backtest results for each threshold
    """
    results = {
        "config_name": config.name,
        "config_description": config.description,
        "symbols": symbols,
        "start_date": start_date,
        "end_date": end_date,
        "threshold_results": []
    }
    
    # Temporarily update ai_service weights
    original_weights = getattr(ai_service, '_weight_config', None)
    ai_service._weight_config = config
    
    try:
        for threshold in signal_thresholds:
            try:
                backtest_result = ai_service.backtest_recommendations(
                    start_date=start_date,
                    end_date=end_date,
                    initial_capital=initial_capital,
                    symbols=symbols,
                    strategy=strategy,
                    signal_threshold=threshold
                )
                
                if backtest_result and backtest_result.get('status') == 'success':
                    metrics = backtest_result.get('metrics', {})
                    threshold_result = {
                        "signal_threshold": threshold,
                        "total_return": metrics.get('total_return', 0.0),
                        "cagr": metrics.get('cagr', 0.0),
                        "sharpe_ratio": metrics.get('sharpe_ratio', 0.0),
                        "max_drawdown": metrics.get('max_drawdown', 0.0),
                        "win_rate": metrics.get('win_rate', 0.0),
                        "num_trades": metrics.get('num_trades', 0)
                    }
                    results["threshold_results"].append(threshold_result)
                else:
                    logger.warning(f"Backtest failed for threshold {threshold}")
                    results["threshold_results"].append({
                        "signal_threshold": threshold,
                        "error": backtest_result.get('error', 'Unknown error') if backtest_result else 'No result'
                    })
            except Exception as e:
                logger.error(f"Error backtesting threshold {threshold}: {e}")
                results["threshold_results"].append({
                    "signal_threshold": threshold,
                    "error": str(e)
                })
    finally:
        # Restore original weights
        if original_weights is not None:
            ai_service._weight_config = original_weights
        elif hasattr(ai_service, '_weight_config'):
            delattr(ai_service, '_weight_config')
    
    return results


def analyze_backtest_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze backtest results and rank configurations.
    
    Args:
        results: List of backtest result dictionaries
    
    Returns:
        Analysis with rankings and recommendations
    """
    analysis = {
        "total_configs": len(results),
        "configs_ranked": [],
        "best_overall": None,
        "best_sharpe": None,
        "best_win_rate": None,
        "best_return": None
    }
    
    best_sharpe = -999
    best_win_rate = -1
    best_return = -999
    
    for result in results:
        config_name = result.get("config_name", "unknown")
        threshold_results = result.get("threshold_results", [])
        
        if not threshold_results:
            continue
        
        # Find best threshold for this config
        best_threshold_result = max(
            threshold_results,
            key=lambda x: (
                x.get("sharpe_ratio", 0) * 0.5 +  # Priority: Sharpe
                x.get("win_rate", 0) * 0.3 +  # Then Win Rate
                x.get("total_return", 0) * 0.2  # Then Return
            ) if "error" not in x else -999
        )
        
        if "error" in best_threshold_result:
            continue
        
        sharpe = best_threshold_result.get("sharpe_ratio", 0)
        win_rate = best_threshold_result.get("win_rate", 0)
        total_return = best_threshold_result.get("total_return", 0)
        
        # Composite score
        composite_score = sharpe * 0.5 + win_rate * 0.3 + min(total_return * 10, 5.0) * 0.2
        
        config_summary = {
            "config_name": config_name,
            "threshold": best_threshold_result.get("signal_threshold"),
            "sharpe_ratio": sharpe,
            "win_rate": win_rate,
            "total_return": total_return,
            "cagr": best_threshold_result.get("cagr", 0),
            "max_drawdown": best_threshold_result.get("max_drawdown", 0),
            "num_trades": best_threshold_result.get("num_trades", 0),
            "composite_score": composite_score
        }
        
        analysis["configs_ranked"].append(config_summary)
        
        # Track best performers
        if sharpe > best_sharpe:
            best_sharpe = sharpe
            analysis["best_sharpe"] = config_summary
        
        if win_rate > best_win_rate:
            best_win_rate = win_rate
            analysis["best_win_rate"] = config_summary
        
        if total_return > best_return:
            best_return = total_return
            analysis["best_return"] = config_summary
    
    # Sort by composite score
    analysis["configs_ranked"].sort(key=lambda x: x["composite_score"], reverse=True)
    
    if analysis["configs_ranked"]:
        analysis["best_overall"] = analysis["configs_ranked"][0]
    
    return analysis


def save_backtest_results(results: List[Dict[str, Any]], filename: str = "weight_optimization_results.json"):
    """Save backtest results to JSON file"""
    results_path = os.path.join(os.path.dirname(__file__), filename)
    
    try:
        with open(results_path, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Saved backtest results to {results_path}")
    except Exception as e:
        logger.error(f"Error saving results: {e}")
