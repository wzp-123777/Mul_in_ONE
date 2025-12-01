"""Session interrupt flags for user interjections.

A lightweight, decoupled mechanism to let the runtime adapter know that
there is a pending user message and the current multi-round agent exchange
should be cut short (after finishing the current round) so the new user
message can be processed with at most one round latency.
"""
from __future__ import annotations

from typing import Dict

# session_id -> bool (interrupt requested)
_INTERRUPT_FLAGS: Dict[str, bool] = {}

def request_interrupt(session_id: str) -> None:
    """Signal that an interrupt is requested for a session."""
    _INTERRUPT_FLAGS[session_id] = True

def consume_interrupt(session_id: str) -> bool:
    """Check and clear interrupt flag for a session.
    Returns True if an interrupt had been requested.
    """
    return _INTERRUPT_FLAGS.pop(session_id, False)

def peek_interrupt(session_id: str) -> bool:
    """Return current interrupt flag without clearing."""
    return _INTERRUPT_FLAGS.get(session_id, False)
