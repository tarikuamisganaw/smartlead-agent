from typing import TypedDict


class AgentState(TypedDict):
    conversation_id: str
    agent_run_id: str
    user_message: str
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
    final_response: str | None
    trace: list[dict]
    errors: list[dict]
