"""Stub file for transformers library"""
from typing import Any, Callable, List, Dict

def pipeline(
    task: str,
    model: str = "",
    device: int = -1,
    **kwargs: Any
) -> Callable[[str], List[Dict[str, Any]]]: ...














