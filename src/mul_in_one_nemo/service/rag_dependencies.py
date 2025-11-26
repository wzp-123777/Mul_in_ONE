"""Lightweight dependency accessors to avoid circular imports."""

from __future__ import annotations

from functools import lru_cache

from .rag_service import RAGService


@lru_cache
def get_rag_service() -> RAGService:
    """Provide a singleton instance of the RAGService without importing heavy dependencies."""
    return RAGService()
