from app.workflow.state import AgentState


def route_after_intent(state: AgentState) -> str:
    if state.get("needs_rag"):
        return "rag"
    return "lead_qualification"
