from sqlalchemy.orm import Session

from langgraph.graph import END, StateGraph

from app.workflow.nodes import (
    action_node,
    final_response_node,
    intent_router_node,
    lead_qualification_node,
    lead_scoring_node,
    rag_node,
    safety_node,
)
from app.workflow.routing import route_after_intent
from app.workflow.state import AgentState


def build_graph(db: Session):
    graph = StateGraph(AgentState)

    graph.add_node("intent_router", intent_router_node)
    graph.add_node("rag", lambda state: rag_node(state, db))
    graph.add_node("lead_qualification", lead_qualification_node)
    graph.add_node("lead_scoring", lead_scoring_node)
    graph.add_node("safety", safety_node)
    graph.add_node("action", lambda state: action_node(state, db))
    graph.add_node("final_response", final_response_node)

    graph.set_entry_point("intent_router")
    graph.add_conditional_edges(
        "intent_router",
        route_after_intent,
        {
            "rag": "rag",
            "lead_qualification": "lead_qualification",
        },
    )
    graph.add_edge("rag", "lead_qualification")
    graph.add_edge("lead_qualification", "lead_scoring")
    graph.add_edge("lead_scoring", "safety")
    graph.add_edge("safety", "action")
    graph.add_edge("action", "final_response")
    graph.add_edge("final_response", END)

    return graph.compile()
