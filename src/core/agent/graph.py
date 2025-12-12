"""LangGraph graph creation and compilation."""

from langgraph.graph import END, START, StateGraph

from core.agent.nodes import (
    call_model_node,
    execute_tools_node,
    input_route,
    invalid_input_node,
    maxed_out_node,
    next_step,
    route_request_node,
    validate_final_answer_node,
    validate_input_node,
)
from core.agent.state import AgentState


def create_graph(checkpointer=None):
    """
    Create and compile the LangGraph ReAct agent workflow.

    Args:
        checkpointer: Optional checkpointer for state persistence (e.g., PostgresSaver)

    Returns:
        Compiled StateGraph ready for invocation

    Graph flow:
        START → validate_input → [invalid_input | route_request]
        route_request → call_model → [tools | finalize | maxed_out]
        tools → call_model (loop)
        [invalid_input | maxed_out | finalize] → validate_final → END
    """
    workflow = StateGraph(AgentState)

    workflow.add_node("validate_input", validate_input_node)
    workflow.add_node("invalid_input", invalid_input_node)
    workflow.add_node("route_request", route_request_node)
    workflow.add_node("call_model", call_model_node)
    workflow.add_node("tools", execute_tools_node)
    workflow.add_node("maxed_out", maxed_out_node)
    workflow.add_node("validate_final", validate_final_answer_node)

    workflow.add_edge(START, "validate_input")

    workflow.add_conditional_edges(
        "validate_input",
        input_route,
        {
            "ok": "route_request",
            "invalid": "invalid_input",
        },
    )

    workflow.add_edge("invalid_input", "validate_final")
    workflow.add_edge("route_request", "call_model")

    workflow.add_conditional_edges(
        "call_model",
        next_step,
        {
            "tools": "tools",
            "finalize": "validate_final",
            "maxed_out": "maxed_out",
        },
    )

    workflow.add_edge("tools", "call_model")
    workflow.add_edge("maxed_out", "validate_final")
    workflow.add_edge("validate_final", END)

    return workflow.compile(checkpointer=checkpointer)
