from __future__ import annotations

from typing import Any, Dict

from agent import code_analysis_tools, database_tools, general_tools
from base_model import anthropic_model, default_model, openai_model
from graph_state import (
    CODE_KEYWORDS,
    DB_KEYWORDS,
    MAX_LLM_CALLS,
    AgentState,
    contains_any,
    get_last_human_text,
    message_text,
)
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from prompts import select_prompt_for_tools


def validate_input_node(state: AgentState) -> Dict[str, Any]:
    """Normalize state and reject obviously invalid inputs."""

    errors: list[str] = list(state.get("errors", []))
    messages: list[BaseMessage] = list(state.get("messages", []))

    if not messages:
        errors.append("No messages provided.")
        messages = [HumanMessage(content="")]

    if not get_last_human_text(messages).strip():
        errors.append("Empty user message.")

    state_defaults: Dict[str, Any] = {
        "messages": messages,
        "selected_model": state.get("selected_model"),
        "selected_tools": list(state.get("selected_tools", [])),
        "llm_calls": int(state.get("llm_calls", 0)),
        "errors": errors,
    }

    # Ensure tools/model always have a safe fallback.
    if state_defaults["selected_model"] is None:
        state_defaults["selected_model"] = default_model
    if not state_defaults["selected_tools"]:
        state_defaults["selected_tools"] = general_tools

    return state_defaults


def input_route(state: AgentState) -> str:
    """Route based on validation outcomes."""

    errors = state.get("errors", [])
    if "Empty user message." in errors or "No messages provided." in errors:
        return "invalid"
    return "ok"


def invalid_input_node(state: AgentState) -> Dict[str, Any]:
    return {
        "messages": [
            AIMessage(
                content=("Please provide a non-empty question/message so I can help.")
            )
        ]
    }


def route_request_node(state: AgentState) -> Dict[str, Any]:
    """Routes the request based on the last human message."""

    last_message_content = get_last_human_text(state["messages"])
    lower_content = last_message_content.lower()

    if contains_any(lower_content, DB_KEYWORDS):
        model = openai_model
        tools_to_use = database_tools
        print("🔵 Selected: OpenAI + Database Tools")

    elif contains_any(lower_content, CODE_KEYWORDS):
        model = anthropic_model
        tools_to_use = code_analysis_tools
        print("🔴 Selected: Claude (Anthropic) + Code Tools")

    else:
        model = default_model
        tools_to_use = general_tools
        print("🟢 Selected: Default Model + General Tools")

    return {
        "selected_model": model,
        "selected_tools": tools_to_use,
    }


def call_model_node(state: AgentState) -> Dict[str, Any]:
    """Call the selected LLM with a prompt aligned to the selected tools."""

    last_user_msg = get_last_human_text(state["messages"])

    selected_prompt = select_prompt_for_tools(
        state["selected_tools"], user_input=last_user_msg
    )

    # prompts return a ChatPromptTemplate; first message is a SystemMessage
    system_instruction = ""
    try:
        system_instruction = message_text(selected_prompt.messages[0])
    except Exception:
        system_instruction = "You are a helpful assistant."

    conversation_msgs = [
        m for m in state["messages"] if not isinstance(m, SystemMessage)
    ]
    final_messages = [SystemMessage(content=system_instruction)] + conversation_msgs

    model = state["selected_model"]
    tools = state["selected_tools"]

    llm_calls = int(state.get("llm_calls", 0)) + 1
    model_with_tools = model.bind_tools(tools)
    response = model_with_tools.invoke(final_messages)

    return {"messages": [response], "llm_calls": llm_calls}


def execute_tools_node(state: AgentState) -> Dict[str, Any]:
    """Execute any tool calls from the last AIMessage."""

    last_message = state["messages"][-1]
    tool_calls = getattr(last_message, "tool_calls", None) or []
    if not tool_calls:
        return {}

    tools_by_name = {tool.name: tool for tool in state["selected_tools"]}
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


def _is_final_ai_message(msg: BaseMessage) -> bool:
    return isinstance(msg, AIMessage) and not (getattr(msg, "tool_calls", None) or [])


def validate_final_answer_node(state: AgentState) -> Dict[str, Any]:
    """Guarantee we end with a printable final AI message."""

    for msg in reversed(state["messages"]):
        if _is_final_ai_message(msg) and message_text(msg).strip():
            return {}

    return {
        "messages": [
            AIMessage(
                content=(
                    "I couldn't produce a final answer reliably. "
                    "Please rephrase the question or provide more details."
                )
            )
        ]
    }


def maxed_out_node(state: AgentState) -> Dict[str, Any]:
    """Stops loops if we hit the max model-call budget."""

    return {
        "messages": [
            AIMessage(
                content=(
                    f"I reached the safety limit of {MAX_LLM_CALLS} model calls while "
                    "trying to complete this request. If you want, I can continue if you "
                    "narrow the question or tell me exactly what output format you need."
                )
            )
        ]
    }


def next_step(state: AgentState) -> str:
    """Decide where to go next: tools vs finalize vs maxed_out."""

    llm_calls = int(state.get("llm_calls", 0))
    last_message = state["messages"][-1]
    tool_calls = getattr(last_message, "tool_calls", None) or []

    if llm_calls >= MAX_LLM_CALLS and tool_calls:
        return "maxed_out"

    if tool_calls:
        return "tools"

    return "finalize"
