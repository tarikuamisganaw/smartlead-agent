from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


IntentLiteral = Literal[
    "faq_question",
    "pricing_question",
    "lead_inquiry",
    "support_request",
    "discount_request",
    "unknown",
]


class ChatRequest(BaseModel):
    conversation_id: str | None = None
    message: str = Field(..., min_length=1)


class ChatResponse(BaseModel):
    conversation_id: str
    agent_run_id: str
    intent: str
    requires_human_approval: bool
    lead_info: dict
    final_response: str
    trace: list[dict]


class RagSearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(default=4, ge=1, le=10)


class IntentResult(BaseModel):
    intent: IntentLiteral
    confidence: float
    needs_rag: bool
    requires_human_approval: bool
    reason: str


class LeadInfo(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    business_type: str | None = None
    service_interest: str | None = None
    budget: int | None = None
    timeline: str | None = None
    missing_fields: list[str] = Field(default_factory=list)


class SafetyResult(BaseModel):
    allowed: bool
    requires_human_approval: bool
    reason: str
    risky_action: str | None = None


class FinalResponse(BaseModel):
    message: str
    next_step: str | None = None


class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    created_at: str


class ConversationResponse(BaseModel):
    id: str
    status: str
    created_at: str
    updated_at: str
    messages: list[MessageResponse]


class LeadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    conversation_id: str
    name: str | None
    email: str | None
    phone: str | None
    business_type: str | None
    service_interest: str | None
    budget: int | None
    timeline: str | None
    lead_score: int | None
    lead_quality: str | None
    status: str
    created_at: str
