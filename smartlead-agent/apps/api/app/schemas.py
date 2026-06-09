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
    anonymous_session_token: str | None = None
    total_latency_ms: int | None = None
    total_model_calls: int | None = None
    model_provider: str | None = None
    model_name: str | None = None


class RagSearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(default=4, ge=1, le=10)


class DocumentUploadRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=180)
    content: str = Field(..., min_length=1, max_length=500_000)


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
    external_sync_status: str | None = None
    external_sync_provider: str | None = None
    external_sync_id: str | None = None
    external_synced_at: str | None = None
    external_sync_error: str | None = None
    last_sync_attempt_at: str | None = None


class AuthRegisterRequest(BaseModel):
    email: str = Field(..., min_length=3)
    password: str = Field(..., min_length=8)
    full_name: str | None = None
    as_owner: bool = False


class AuthLoginRequest(BaseModel):
    email: str = Field(..., min_length=3)
    password: str = Field(..., min_length=1)


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str | None = None
    is_active: bool
    created_at: str


class MembershipResponse(BaseModel):
    organization_id: str
    organization_name: str
    role: str


class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class AuthMeResponse(BaseModel):
    user: UserResponse
    memberships: list[MembershipResponse]


class AnonymousSessionResponse(BaseModel):
    anonymous_session_id: str
    session_token: str


class ClaimAnonymousSessionRequest(BaseModel):
    session_token: str = Field(..., min_length=16)
