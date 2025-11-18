"""Stub file for Prophet library"""
from typing import Any

class Prophet:
    def __init__(
        self,
        daily_seasonality: bool = True,
        weekly_seasonality: bool = True,
        yearly_seasonality: bool = True,
        changepoint_prior_scale: float = 0.05,
        growth: str = "linear"
    ) -> None: ...
    
    def add_regressor(self, name: str) -> None: ...
    def add_seasonality(
        self,
        name: str,
        period: float,
        fourier_order: int
    ) -> None: ...
    def fit(self, df: Any) -> None: ...
    def predict(self, df: Any) -> Any: ...
    def make_future_dataframe(self, periods: int) -> Any: ...














