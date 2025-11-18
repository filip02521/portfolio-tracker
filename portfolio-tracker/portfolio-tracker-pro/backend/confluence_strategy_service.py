"""Legacy Confluence Strategy wrapper."""

from typing import Any, Dict

from due_diligence_service import DueDiligenceService


class ConfluenceStrategyService:
    """
    Legacy facade maintained for backwards compatibility.

    The previous confluence trading implementation has been deprecated in favour of
    the Due Diligence 360° scoring engine. Existing callers receive deprecation notices
    together with the new analytical payload so they can migrate gracefully.
    """

    def __init__(self, market_data_service):
        self.due_diligence = DueDiligenceService(market_data_service=market_data_service)

    def analyze_entry_signals(self, symbol: str, interval: str = "4h", timeframe: str = "4h") -> Dict[str, Any]:
        result = self.due_diligence.evaluate(symbol)
        return {
            "entry_signal": "deprecated",
            "confidence": result.confidence,
            "confluence_score": result.normalized_score,
            "entry_price": None,
            "entry_reasons": ["Due Diligence 360° supersedes legacy confluence strategy."],
            "confluence_conditions": [],
            "due_diligence": result.dict(),
            "interval": interval,
            "timeframe": timeframe,
            "deprecated": True,
            "message": (
                "Confluence strategy has been replaced by the Due Diligence 360° framework. "
                "Use /analysis/due-diligence endpoints for actionable insights."
            ),
        }
    
    def analyze_exit_signals(
        self,
        symbol: str,
        entry_price: float,
        entry_date: str,
        current_price: float,
        current_date: str,
        interval: str = "4h",
        portfolio_value: float = 10000.0,
        risk_per_trade: float = 0.02,
    ) -> Dict[str, Any]:
        result = self.due_diligence.evaluate(symbol)
        return {
            "exit_signal": "hold",
            "exit_reason": "deprecated",
            "message": (
                "Legacy exit analyser is deprecated. Use Due Diligence 360° outputs to inform risk management."
            ),
            "due_diligence": result.dict(),
            "deprecated": True,
        }
    
    def backtest_confluence_strategy(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        initial_capital: float,
        interval: str = "4h",
        risk_per_trade: float = 0.02,
        min_confluence_score: int = 4,
        min_confidence: float = 0.7,
    ) -> Dict[str, Any]:
        return {
            "status": "deprecated",
            "message": (
                "Legacy confluence backtest has been retired. "
                "Due Diligence 360° focuses on long-horizon asset quality assessment."
            ),
        }

