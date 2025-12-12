"""PostgreSQL checkpointer for LangGraph state persistence."""

import os
from contextlib import asynccontextmanager, contextmanager
from typing import AsyncGenerator, Generator

from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from config.settings import settings


def get_db_uri() -> str:
    """
    Get PostgreSQL connection URI for checkpointer.

    Uses DATABASE_URL from environment or settings.
    """
    return settings.DATABASE_URL or os.getenv(
        "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/postgres"
    )


@contextmanager
def get_checkpointer() -> Generator[PostgresSaver, None, None]:
    """
    Get synchronous PostgreSQL checkpointer context manager.

    Usage:
        with get_checkpointer() as checkpointer:
            graph = create_graph(checkpointer=checkpointer)
            result = graph.invoke(state, config)

    Note: Call checkpointer.setup() on first run to create tables.
    """
    db_uri = get_db_uri()
    with PostgresSaver.from_conn_string(db_uri) as checkpointer:
        yield checkpointer


@asynccontextmanager
async def get_async_checkpointer() -> AsyncGenerator[AsyncPostgresSaver, None]:
    """
    Get asynchronous PostgreSQL checkpointer context manager.

    Usage:
        async with get_async_checkpointer() as checkpointer:
            graph = create_graph(checkpointer=checkpointer)
            result = await graph.ainvoke(state, config)

    Note: Call await checkpointer.setup() on first run to create tables.
    """
    db_uri = get_db_uri()
    async with AsyncPostgresSaver.from_conn_string(db_uri) as checkpointer:
        yield checkpointer


def create_thread_config(thread_id: str, checkpoint_id: str | None = None) -> dict:
    """
    Create config dict for thread-scoped checkpoints.

    Args:
        thread_id: Unique identifier for conversation thread
        checkpoint_id: Optional specific checkpoint to resume from

    Returns:
        Configuration dict for graph invocation

    Example:
        config = create_thread_config("user-123")
        result = graph.invoke(state, config)
    """
    configurable = {"thread_id": thread_id}
    if checkpoint_id:
        configurable["checkpoint_id"] = checkpoint_id

    return {"configurable": configurable}
