"""
Session Memory Management
"""
from langchain_core.chat_history import InMemoryChatMessageHistory

# Store conversation histories per session
_session_stores: dict[str, InMemoryChatMessageHistory] = {}


def get_session_history(session_id: str) -> InMemoryChatMessageHistory:
    """Get or create chat history for a session."""
    if session_id not in _session_stores:
        _session_stores[session_id] = InMemoryChatMessageHistory()
    return _session_stores[session_id]


def clear_session(session_id: str) -> bool:
    """Clear a session. Returns True if existed."""
    if session_id in _session_stores:
        _session_stores[session_id].clear()
        return True
    return False


def session_exists(session_id: str) -> bool:
    """Check if session exists."""
    return session_id in _session_stores
