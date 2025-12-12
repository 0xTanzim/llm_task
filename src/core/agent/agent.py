"""LangChain + LangGraph Agent Implementation."""

from typing import Literal

from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from typing_extensions import Annotated, TypedDict

from core.base_llm.openAi import get_llm
from core.memory.checkpointer import get_checkpointer


class AgentState(TypedDict):
    """Agent state with message history."""

    messages: Annotated[list, add_messages]


@tool
def search_web(query: str) -> str:
    """Search the web for current information.

    Args:
        query: Search terms to look for

    Returns:
        str: Search results
    """
    try:
        from langchain_tavily import TavilySearch

        search = TavilySearch(max_results=3)
        results = search.invoke(query)
        return str(results)
    except ImportError:
        return "Tavily search not available. Please install langchain-tavily."
    except Exception as e:
        return f"Search error: {str(e)}"


@tool
def calculate(expression: str) -> str:
    """Evaluate mathematical expressions safely.

    Args:
        expression: Mathematical expression to evaluate (e.g., '2 + 2', '10 * 5')

    Returns:
        str: Calculation result
    """
    try:
        allowed_names = {
            "abs": abs,
            "round": round,
            "min": min,
            "max": max,
            "sum": sum,
            "pow": pow,
        }
        result = eval(expression, {"__builtins__": {}}, allowed_names)
        return str(result)
    except Exception as e:
        return f"Calculation error: {str(e)}"


def create_agent():
    """Create LangGraph agent with tools and memory.

    Returns:
        Compiled LangGraph agent with checkpointing
    """
    llm = get_llm()
    tools = [search_web, calculate]
    llm_with_tools = llm.bind_tools(tools)

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are a helpful AI assistant with web search and calculation capabilities.
Provide accurate, concise responses. Use tools when needed to answer questions.""",
            ),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )

    def call_model(state: AgentState) -> dict:
        """Invoke model with current state."""
        messages = state["messages"]

        prompt_value = prompt.invoke({"messages": messages})
        response = llm_with_tools.invoke(prompt_value)

        return {"messages": [response]}

    def should_continue(state: AgentState) -> Literal["tools", "__end__"]:
        """Determine next step based on tool calls."""
        messages = state["messages"]
        last_message = messages[-1]

        if isinstance(last_message, AIMessage) and last_message.tool_calls:
            return "tools"
        return "__end__"

    workflow = StateGraph(AgentState)

    workflow.add_node("agent", call_model)
    workflow.add_node("tools", ToolNode(tools))

    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges(
        "agent", should_continue, {"tools": "tools", "__end__": END}
    )
    workflow.add_edge("tools", "agent")

    checkpointer = get_checkpointer()
    return workflow.compile(checkpointer=checkpointer)
