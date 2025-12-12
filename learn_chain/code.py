from __future__ import annotations

from collections.abc import Callable
from typing import Any, cast

from langchain.agents import create_agent
from langchain.agents.middleware import ModelRequest, ModelResponse, wrap_model_call
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from agent import (
    all_tools,
    code_analysis_tools,
    database_tools,
    general_tools,
)
from base_model import (
    anthropic_model,
    default_model,
    gemini_model,
    openai_model,
)
from prompts import dynamic_template_selector



def _message_text(message: Any) -> str:
    """Best-effort conversion of a LangChain message to plain text."""

    # Prefer LangChain's standardized accessor (handles str vs content blocks).
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


@wrap_model_call
def dynamic_agent_middleware(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse],
) -> ModelResponse:
    """Dynamicalldy select model, tools, AND system prompt based on user query"""

    messages = request.messages

    # In a chat history, we might want to look at the last HumanMessage
    last_message_content: str = ""
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            last_message_content = _message_text(msg)
            break

    if not last_message_content and messages:
        last_message_content = _message_text(messages[-1])

    user_input_lower = last_message_content.casefold()

    # 1. Select Model and Tools
    if any(
        word in user_input_lower
        for word in ["code", "function", "debug", "python", "program"]
    ):
        model = anthropic_model
        tools_to_use = code_analysis_tools
        print("🔴 Selected: Claude (Anthropic) + Code Tools")

    elif any(
        word in user_input_lower
        for word in [
            "database",
            "sql",
            "query",
            "data",
            "table",
            "schema",
            "db",
            "records",
        ]
    ):
        model = openai_model
        tools_to_use = database_tools
        print("🔵 Selected: OpenAI + Database Tools")

    else:
        model = gemini_model
        tools_to_use = general_tools
        print("🟢 Selected: Gemini + General Tools")

    # 2. Select System Prompt
    selected_prompt_template = dynamic_template_selector(last_message_content)

    # Extract system message content
    first_msg = selected_prompt_template.messages[0]

    system_instruction = _message_text(first_msg)
    if not system_instruction:
        system_instruction = "You are a helpful assistant."

    # 3. Update Messages with System Prompt
    new_messages = list(messages)

    # Check if the first message is a SystemMessage
    if new_messages and isinstance(new_messages[0], SystemMessage):
        # Replace existing system message
        print("🔄 Updating System Prompt")
        new_messages[0] = SystemMessage(content=system_instruction)
    else:
        # Prepend system message
        print("➕ Adding System Prompt")
        new_messages.insert(0, SystemMessage(content=system_instruction))

    # 4. Bind tools to model
    model_with_tools = cast(BaseChatModel, model.bind_tools(tools=tools_to_use))

    # 5. Call handler with updated request
    return handler(request.override(model=model_with_tools, messages=new_messages))


def main():
    print("Hello from lang-chain!")

    agent = create_agent(
        model=default_model,
        tools=all_tools,
        middleware=[dynamic_agent_middleware],
    )

    # Example 1: General Question
    print("\n--- TASK 1: GENERAL QUESTION ---")
    result1 = agent.invoke(
        {
            "messages": [
                HumanMessage(content="What is the latest in artificial intelligence? why is ai important? Bad side of ai in 2030.")
            ]
        }
    )
    print("Result 1:", result1)

    # Example 2: Code Task
    print("\n--- TASK 2: CODE ANALYSIS ---")
    result2 = agent.invoke(
        {
            "messages": [
                HumanMessage(
                    content="Write a Python function that takes a list of numbers and returns the sum of even numbers. also factorial of a number."
                )
            ]
        }
    )
    print("Result 2:", result2)

    # Example 3: Database Task
    print("\n--- TASK 3: DATABASE QUERY ---")
    result3 = agent.invoke(
        {
            "messages": [
                HumanMessage(
                    content="give me the highest ordered products from database top 2 records."
                )
            ]
        }
    )
    print("Result 3:", result3)


if __name__ == "__main__":
    main()
