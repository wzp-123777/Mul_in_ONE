"""Lightweight dependency accessors to avoid circular imports."""

from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .rag_service import RAGService


@lru_cache
def get_rag_service() -> "RAGService":
    """Provide a singleton instance of the RAGService, delegating to the main dependencies module."""
    # Lazy import to avoid circular dependencies
    from mul_in_one_nemo.service.dependencies import get_rag_service as _get_service
    return _get_service()
