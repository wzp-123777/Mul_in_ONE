"""Context management for multi-user RAG operations.

Provides thread-safe context storage for username and persona_id
that tools can access during execution without exposing these
system metadata to the LLM.
"""

import contextvars
from typing import Optional

# Context variables for user and persona
_user_context: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    'user_context', default=None
)
_persona_context: contextvars.ContextVar[Optional[int]] = contextvars.ContextVar(
    'persona_context', default=None
)


def set_rag_context(username: str, persona_id: int) -> None:
    """Set the current RAG context for this async task.
    
    Args:
        username: User identifier for user isolation
        persona_id: Persona identifier for the user
    """
    _user_context.set(username)
    _persona_context.set(persona_id)


def get_rag_context() -> tuple[Optional[str], Optional[int]]:
    """Get the current RAG context.
    
    Returns:
        Tuple of (username, persona_id)
    """
    return _user_context.get(), _persona_context.get()


def clear_rag_context() -> None:
    """Clear the RAG context for this async task."""
    _user_context.set(None)
    _persona_context.set(None)
