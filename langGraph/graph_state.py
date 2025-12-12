from __future__ import annotations

from operator import add as add_messages
from typing import Annotated, Any, List, TypedDict

from langchain_core.messages import BaseMessage, HumanMessage


class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    selected_model: Any
    selected_tools: List[Any]
    llm_calls: int
    errors: List[str]


DB_KEYWORDS = {"database", "sql", "data", "schema", "query", "postgres", "mysql"}
CODE_KEYWORDS = {
    "code",
    "bug",
    "error",
    "stack trace",
    "function",
    "class",
    "python",
    "typescript",
}

MAX_LLM_CALLS = 6


def message_text(message: Any) -> str:
    """Best-effort conversion of a LangChain message to plain text."""

    text = getattr(message, "text", None)
    if text is not None:
        return str(text)

    content = getattr(message, "content", "")
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                maybe_text = item.get("text")
                if isinstance(maybe_text, str):
                    parts.append(maybe_text)
        return "".join(parts)

    return str(content)


def get_last_human_text(messages: List[BaseMessage]) -> str:
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            return message_text(msg)
    return ""


def contains_any(text: str, keywords: set[str]) -> bool:
    return any(k in text for k in keywords)
