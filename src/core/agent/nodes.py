"""Node functions for the LangGraph agent."""

from typing import Any

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)

from core.agent.state import AgentState
from core.prompts.templates import select_prompt_for_tools

# Configuration constants
MAX_LLM_CALLS = 6
DB_KEYWORDS = {
    "database",
    "sql",
    "data",
    "schema",
    "query",
    "postgres",
    "mysql",
    "table",
}
CODE_KEYWORDS = {
    "code",
    "bug",
    "error",
    "function",
    "class",
    "python",
    "debug",
    "refactor",
}


def message_text(message: Any) -> str:
    """Extract text content from a message."""
    if hasattr(message, "content"):
        content = message.content
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, str):
                    parts.append(item)
                elif isinstance(item, dict) and "text" in item:
                    parts.append(str(item["text"]))
            return "".join(parts)
    return str(message)


def get_last_human_text(messages: list[BaseMessage]) -> str:
    """Get the text content of the last human message."""
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            return message_text(msg)
    return ""


def validate_input_node(state: AgentState) -> dict[str, Any]:
    """
    Validate and normalize input state.

    Ensures messages exist and are non-empty.
    Sets default values for model and tools if not provided.
    """
    errors: list[str] = list(state.get("errors", []))
    messages: list[BaseMessage] = list(state.get("messages", []))

    if not messages:
        errors.append("No messages provided.")
        messages = [HumanMessage(content="")]

    if not get_last_human_text(messages).strip():
        errors.append("Empty user message.")

    return {
        "messages": messages,
        "selected_model": state.get("selected_model"),
        "selected_tools": list(state.get("selected_tools", [])),
        "llm_calls": int(state.get("llm_calls", 0)),
        "errors": errors,
    }


def input_route(state: AgentState) -> str:
    """Route based on validation results."""
    errors = state.get("errors", [])
    if "Empty user message." in errors or "No messages provided." in errors:
        return "invalid"
    return "ok"


def invalid_input_node(state: AgentState) -> dict[str, Any]:
    """Handle invalid input."""
    return {
        "messages": [
            AIMessage(content="Please provide a non-empty question so I can help you.")
        ]
    }


def route_request_node(state: AgentState) -> dict[str, Any]:
    """
    Route request to appropriate model and toolset.

    Uses keyword matching to determine if the query is:
    - Database-related (DB_KEYWORDS)
    - Code-related (CODE_KEYWORDS)
    - General query (default)
    """
    from core.tools.code import code_analysis_tools
    from core.tools.database import database_tools
    from core.tools.general import general_tools

    last_message = get_last_human_text(state["messages"])
    lower_content = last_message.lower()

    # Check for database keywords
    if any(keyword in lower_content for keyword in DB_KEYWORDS):
        model_type = "openai"
        tool_names = [tool.name for tool in database_tools]
        print("🔵 Selected: OpenAI + Database Tools")
    # Check for code keywords
    elif any(keyword in lower_content for keyword in CODE_KEYWORDS):
        model_type = "anthropic"
        tool_names = [tool.name for tool in code_analysis_tools]
        print("🔴 Selected: Anthropic + Code Tools")
    # Default to general
    else:
        model_type = "default"
        tool_names = [tool.name for tool in general_tools]
        print("🟢 Selected: Default Model + General Tools")

    return {
        "selected_model": model_type,
        "selected_tools": tool_names,
    }


def call_model_node(state: AgentState) -> dict[str, Any]:
    """
    Invoke the LLM with appropriate prompt and tools.

    Constructs system message from prompt template,
    binds tools to model, and invokes with conversation history.
    Includes automatic retry with exponential backoff for failures.
    """
    from config.settings import get_model
    from core.tools.code import code_analysis_tools
    from core.tools.database import database_tools
    from core.tools.general import general_tools
    from core.utils.retry import retry_with_exponential_backoff

    last_user_msg = get_last_human_text(state["messages"])

    # Reconstruct model from identifier
    model_type = state["selected_model"]
    model = get_model(model_type)

    # Reconstruct tools from names
    all_tools = database_tools + code_analysis_tools + general_tools
    tool_names = state["selected_tools"]
    tools = [tool for tool in all_tools if tool.name in tool_names]

    # Select appropriate prompt template
    selected_prompt = select_prompt_for_tools(tools, user_input=last_user_msg)

    # Extract system instruction from prompt template
    system_instruction = "You are a helpful assistant."
    try:
        system_instruction = message_text(selected_prompt.messages[0])
    except Exception:
        pass

    # Build message list (exclude existing system messages)
    conversation_msgs = [
        m for m in state["messages"] if not isinstance(m, SystemMessage)
    ]
    final_messages = [SystemMessage(content=system_instruction)] + conversation_msgs

    # Bind tools and invoke model with retry logic
    llm_calls = int(state.get("llm_calls", 0)) + 1

    @retry_with_exponential_backoff(
        max_retries=3,
        initial_delay=1.0,
        backoff_factor=2.0,
        retry_on=(ConnectionError, TimeoutError, Exception),
    )
    def invoke_with_retry():
        model_with_tools = model.bind_tools(tools)
        return model_with_tools.invoke(final_messages)

    try:
        response = invoke_with_retry()
    except Exception as e:
        # Fallback error message if all retries fail
        response = AIMessage(
            content=f"I encountered an error calling the model: {str(e)}. Please try again."
        )

    return {"messages": [response], "llm_calls": llm_calls}


def execute_tools_node(state: AgentState) -> dict[str, Any]:
    """
    Execute tool calls from the last AI message.

    Processes tool_calls from AIMessage, invokes tools,
    and returns ToolMessage results.
    """
    from core.tools.code import code_analysis_tools
    from core.tools.database import database_tools
    from core.tools.general import general_tools

    last_message = state["messages"][-1]
    tool_calls = getattr(last_message, "tool_calls", None) or []

    if not tool_calls:
        return {}

    # Reconstruct tools from names
    all_tools = database_tools + code_analysis_tools + general_tools
    tool_names = state["selected_tools"]
    tools = [tool for tool in all_tools if tool.name in tool_names]
    tools_by_name = {tool.name: tool for tool in tools}
    tool_results: list[ToolMessage] = []

    for tool_call in tool_calls:
        tool_name = tool_call.get("name")
        tool_input = tool_call.get("args")
        tool_call_id = tool_call.get("id")

        if tool_name not in tools_by_name:
            tool_results.append(
                ToolMessage(
                    content=f"❌ Unknown tool: {tool_name}",
                    tool_call_id=str(tool_call_id),
                    name=str(tool_name),
                )
            )
            continue

        tool = tools_by_name[tool_name]
        try:
            result = tool.invoke(tool_input)
            tool_results.append(
                ToolMessage(
                    content=str(result),
                    tool_call_id=str(tool_call_id),
                    name=str(tool_name),
                )
            )
        except Exception as exc:
            tool_results.append(
                ToolMessage(
                    content=f"❌ Tool error ({tool_name}): {exc}",
                    tool_call_id=str(tool_call_id),
                    name=str(tool_name),
                )
            )

    return {"messages": tool_results}


def validate_final_answer_node(state: AgentState) -> dict[str, Any]:
    """
    Ensure we have a final answer from the agent.

    Checks if the last message is a valid AI response without tool calls.
    If not, generates a fallback message.
    """
    for msg in reversed(state["messages"]):
        if isinstance(msg, AIMessage) and not getattr(msg, "tool_calls", None):
            if message_text(msg).strip():
                return {}

    return {
        "messages": [
            AIMessage(
                content=(
                    "I couldn't produce a final answer. "
                    "Please rephrase your question or provide more details."
                )
            )
        ]
    }


def maxed_out_node(state: AgentState) -> dict[str, Any]:
    """Handle case where max LLM calls limit is reached."""
    return {
        "messages": [
            AIMessage(
                content=(
                    f"I reached the safety limit of {MAX_LLM_CALLS} model calls. "
                    "Please try narrowing your question or being more specific."
                )
            )
        ]
    }


def next_step(state: AgentState) -> str:
    """
    Determine next step in the agent flow.

    Returns:
        "maxed_out": If max LLM calls reached
        "tools": If last message has tool calls
        "finalize": If ready to return final answer
    """
    llm_calls = int(state.get("llm_calls", 0))
    last_message = state["messages"][-1]
    tool_calls = getattr(last_message, "tool_calls", None) or []

    if llm_calls >= MAX_LLM_CALLS and tool_calls:
        return "maxed_out"

    if tool_calls:
        return "tools"

    return "finalize"
