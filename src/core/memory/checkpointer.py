"""Simple memory checkpointer for conversation history."""

from langgraph.checkpoint.memory import MemorySaver


def get_checkpointer():
    """Get memory checkpointer for agent."""
    return MemorySaver()
