from __future__ import annotations

from graph_nodes import (
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
from graph_state import AgentState
from langgraph.graph import END, START, StateGraph


def create_app():
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

    return workflow.compile()
