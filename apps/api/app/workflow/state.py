from typing import TypedDict


class AgentState(TypedDict):
    conversation_id: str
    agent_run_id: str
    user_message: str
    organization_id: str | None
    user_id: str | None
    anonymous_session_id: str | None
    conversation_history: list[dict]
    existing_lead: dict | None
    intent: str | None
    intent_confidence: float | None
    needs_rag: bool
    retrieved_docs: list[dict]
    lead_info: dict
    missing_lead_fields: list[str]
    lead_score: int | None
    lead_quality: str | None
    requires_human_approval: bool
    approval_reason: str | None
    selected_action: str | None
    tool_results: list[dict]
    model_provider: str | None
    model_name: str | None
    model_calls: int
    estimated_cost: float
    final_response: str | None
    trace: list[dict]
    errors: list[dict]
    fatal_error: bool
