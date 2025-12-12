"""Agent state schema for LangGraph."""

from typing import Annotated

from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages  # LangGraph's built-in message reducer
from typing_extensions import TypedDict


class AgentState(TypedDict):
    """
    State schema for the ReAct agent.

    Attributes:
        messages: Conversation history with reducer for concatenation
        selected_model: Currently selected LLM model (stored as string identifier)
        selected_tools: List of tool names (strings) available to the agent
        llm_calls: Counter for number of model invocations
        errors: List of error messages encountered
    """

    messages: Annotated[list[BaseMessage], add_messages]
    selected_model: str  # Model identifier: 'default', 'openai', 'anthropic'
    selected_tools: list[str]  # Tool names, not tool objects
    llm_calls: int
    errors: list[str]
