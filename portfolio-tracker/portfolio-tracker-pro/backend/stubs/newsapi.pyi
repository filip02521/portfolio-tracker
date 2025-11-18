"""Stub file for newsapi library"""
from typing import Any, Dict, List, Optional

class NewsApiClient:
    def __init__(self, api_key: str) -> None: ...
    def get_everything(
        self,
        q: Optional[str] = None,
        sources: Optional[str] = None,
        domains: Optional[str] = None,
        from_param: Optional[str] = None,
        to: Optional[str] = None,
        language: Optional[str] = None,
        sort_by: Optional[str] = None,
        page: int = 1,
        page_size: int = 100
    ) -> Dict[str, Any]: ...
    def get_top_headlines(
        self,
        q: Optional[str] = None,
        sources: Optional[str] = None,
        category: Optional[str] = None,
        language: Optional[str] = None,
        country: Optional[str] = None,
        page: int = 1,
        page_size: int = 100
    ) -> Dict[str, Any]: ...














