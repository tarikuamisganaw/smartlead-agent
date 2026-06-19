from time import perf_counter
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.evals.evaluator import load_eval_cases, read_latest_eval_results, run_all_evals
from app.models import (
    AnonymousSession,
    AgentRun,
    AgentTraceEvent,
    Conversation,
    Document,
    DocumentChunk,
    HumanApproval,
    Lead,
    Message,
    ToolCall,
    utc_now,
)
from app.schemas import ChatRequest, ChatResponse, DocumentUploadRequest, RagSearchRequest
from app.services.auth_service import (
    get_current_user_optional,
    get_current_user_required,
    get_anonymous_session_by_token,
    get_or_create_anonymous_session,
    get_or_create_default_organization,
)
from app.services.conversation_service import add_message, get_conversation_with_messages, get_or_create_conversation
from app.services.document_service import (
    create_document_from_content,
    default_demo_data_dir,
    ingest_documents,
    list_documents_with_chunk_counts,
)
from app.services.embedding_service import active_embedding_model_name
from app.services.integrations.lead_sync_provider import get_lead_sync_provider
from app.services.integrations.notification_provider import get_notification_providers
from app.services.lead_service import get_latest_lead_for_conversation, lead_to_dict, list_leads, sync_lead_external
from app.services.metrics_service import collect_agent_run_metrics, default_model_metadata
from app.services.performance_service import recent_performance
from app.services.rag_service import search_docs
from app.services.rag_service import invalidate_rag_index
from app.services.rbac_service import ADMIN_READ_ROLES, require_admin_read, require_admin_write, require_conversation_access, user_has_org_role
from app.services.trace_service import add_trace_event_to_state, now_ms, persist_trace_events
from app.workflow.graph import build_graph
from app.workflow.state import AgentState

router = APIRouter()


@router.get("/health")
async def health(db: Session = Depends(get_db)) -> dict:
    settings = get_settings()
    database_connected = _database_connected(db)
    return {
        "status": "ok",
        "service": settings.service_name,
        "environment": settings.environment,
        "model_provider": settings.model_provider,
        "auth_enabled": settings.auth_enabled,
        "database_connected": database_connected,
        "database_kind": _database_kind(settings.database_url),
        "rag_provider": settings.rag_provider,
        "embedding_provider": settings.embedding_provider,
        "embedding_model": active_embedding_model_name(),
    }


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    http_request: Request,
    db: Session = Depends(get_db),
    x_anonymous_session_token: str | None = Header(default=None, alias="X-Anonymous-Session-Token"),
) -> ChatResponse:
    request_started = perf_counter()
    settings = get_settings()
    user = get_current_user_optional(http_request, db)
    organization = get_or_create_default_organization(db)
    anonymous_session: AnonymousSession | None = None
    anonymous_session_token: str | None = None
    if not user:
        anonymous_session = get_or_create_anonymous_session(db, x_anonymous_session_token)
        anonymous_session_token = anonymous_session.session_token

    conversation = get_or_create_conversation(
        db,
        request.conversation_id,
        organization_id=organization.id,
        user_id=user.id if user else None,
        anonymous_session_id=anonymous_session.id if anonymous_session else None,
    )
    _require_chat_conversation_access(db, http_request, conversation, anonymous_session)
    add_message(
        db,
        conversation_id=conversation.id,
        role="user",
        content=request.message,
        user_id=user.id if user else None,
        anonymous_session_id=anonymous_session.id if anonymous_session else None,
    )
    conversation_with_messages = get_conversation_with_messages(db, conversation.id)
    existing_lead = get_latest_lead_for_conversation(db, conversation.id)
    model_provider, model_name = default_model_metadata()

    agent_run = AgentRun(
        conversation_id=conversation.id,
        organization_id=organization.id,
        user_id=user.id if user else None,
        anonymous_session_id=anonymous_session.id if anonymous_session else None,
        user_message=request.message,
        status="success",
        model_provider=model_provider,
        model_name=model_name,
    )
    db.add(agent_run)
    db.commit()
    db.refresh(agent_run)

    initial_state: AgentState = {
        "conversation_id": conversation.id,
        "agent_run_id": agent_run.id,
        "user_message": request.message,
        "organization_id": organization.id,
        "user_id": user.id if user else None,
        "anonymous_session_id": anonymous_session.id if anonymous_session else None,
        "conversation_history": [
            {
                "role": message.role,
                "content": message.content,
                "created_at": message.created_at.isoformat(),
            }
            for message in (conversation_with_messages.messages if conversation_with_messages else [])
        ],
        "existing_lead": lead_to_dict(existing_lead),
        "intent": None,
        "intent_confidence": None,
        "needs_rag": False,
        "retrieved_docs": [],
        "lead_info": {},
        "missing_lead_fields": [],
        "lead_score": None,
        "lead_quality": None,
        "requires_human_approval": False,
        "approval_reason": None,
        "selected_action": None,
        "tool_results": [],
        "model_provider": model_provider,
        "model_name": model_name,
        "model_calls": 0,
        "estimated_cost": 0,
        "final_response": None,
        "trace": [],
        "errors": [],
        "fatal_error": False,
    }

    try:
        graph = build_graph(db)
        final_state = graph.invoke(initial_state)
    except Exception as exc:  # pragma: no cover - defensive route fallback
        db.rollback()
        final_state = initial_state
        final_state["errors"].append({"node_name": "workflow", "error": str(exc)})
        final_state["fatal_error"] = True
        final_state["final_response"] = "Sorry, something went wrong while processing that request."
        add_trace_event_to_state(
            final_state,
            agent_name="smartlead-agent",
            node_name="workflow",
            input_summary="Workflow invocation failed.",
            output_summary="Returned safe fallback response.",
            status="failed",
            error_message=str(exc),
            latency_ms=now_ms(request_started),
        )

    if not final_state.get("final_response"):
        final_state["final_response"] = "Sorry, I could not produce a response for that request."

    agent_run.final_response = final_state["final_response"]
    agent_run.finished_at = utc_now()
    agent_run.total_latency_ms = now_ms(request_started)
    metrics = collect_agent_run_metrics(final_state)
    agent_run.total_model_calls = metrics["total_model_calls"]
    agent_run.estimated_cost = metrics["estimated_cost"]
    agent_run.model_provider = metrics["model_provider"]
    agent_run.model_name = metrics["model_name"]
    if final_state.get("fatal_error"):
        agent_run.status = "failed"
    elif final_state.get("requires_human_approval"):
        agent_run.status = "pending_approval"
    else:
        agent_run.status = "success"
    db.add(agent_run)
    db.commit()

    add_message(
        db,
        conversation_id=conversation.id,
        role="assistant",
        content=final_state["final_response"],
        user_id=user.id if user else None,
        anonymous_session_id=anonymous_session.id if anonymous_session else None,
    )
    persist_trace_events(db, agent_run.id, final_state.get("trace", []))
    can_view_internal_data = _can_return_trace(db, user, organization.id, settings.auth_enabled)
    trace = final_state.get("trace", []) if can_view_internal_data else []
    lead_info = {
        **(final_state.get("lead_info") or {}),
        "lead_score": final_state.get("lead_score"),
        "lead_quality": final_state.get("lead_quality"),
    } if can_view_internal_data else {}

    return ChatResponse(
        conversation_id=conversation.id,
        agent_run_id=agent_run.id,
        intent=final_state.get("intent") or "unknown",
        requires_human_approval=bool(final_state.get("requires_human_approval")),
        lead_info=lead_info,
        final_response=final_state["final_response"],
        trace=trace,
        anonymous_session_token=anonymous_session_token,
        total_latency_ms=agent_run.total_latency_ms if can_view_internal_data else None,
        total_model_calls=agent_run.total_model_calls if can_view_internal_data else None,
        model_provider=agent_run.model_provider if can_view_internal_data else None,
        model_name=agent_run.model_name if can_view_internal_data else None,
    )


@router.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str, request: Request, db: Session = Depends(get_db)) -> dict:
    conversation = get_conversation_with_messages(db, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    require_conversation_access(db, request, conversation)

    return _conversation_detail(db, conversation)


@router.get("/agent-runs/{agent_run_id}/trace")
async def get_agent_run_trace(agent_run_id: str, request: Request, db: Session = Depends(get_db)) -> dict:
    agent_run = db.get(AgentRun, agent_run_id)
    if not agent_run:
        raise HTTPException(status_code=404, detail="Agent run not found.")
    require_admin_read(db, request)

    statement = (
        select(AgentTraceEvent)
        .where(AgentTraceEvent.agent_run_id == agent_run_id)
        .order_by(AgentTraceEvent.step_number)
    )
    events = db.scalars(statement).all()
    tool_statement = select(ToolCall).where(ToolCall.agent_run_id == agent_run_id).order_by(ToolCall.created_at)
    tool_calls = db.scalars(tool_statement).all()
    return {
        "agent_run_id": agent_run_id,
        "trace": [
            {
                "id": event.id,
                "step_number": event.step_number,
                "agent_name": event.agent_name,
                "node_name": event.node_name,
                "input_summary": event.input_summary,
                "output_summary": event.output_summary,
                "tool_name": event.tool_name,
                "status": event.status,
                "error_message": event.error_message,
                "latency_ms": event.latency_ms,
                "created_at": event.created_at.isoformat(),
            }
            for event in events
        ],
        "tool_calls": [_tool_call_to_dict(tool_call) for tool_call in tool_calls],
    }


@router.get("/leads")
async def get_leads(request: Request, db: Session = Depends(get_db)) -> dict:
    require_admin_read(db, request)
    return {"leads": [lead_to_dict(lead) for lead in list_leads(db)]}


@router.post("/leads/{lead_id}/sync")
async def sync_lead(lead_id: str, request: Request, db: Session = Depends(get_db)) -> dict:
    require_admin_write(db, request)
    lead = db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found.")

    result = sync_lead_external(db, lead, force=True)
    db.refresh(lead)
    return {"lead": lead_to_dict(lead), "sync_result": result}


@router.get("/integrations/status")
async def get_integrations_status(request: Request, db: Session = Depends(get_db)) -> dict:
    require_admin_read(db, request)
    settings = get_settings()
    lead_sync_provider = get_lead_sync_provider()
    notification_providers = get_notification_providers()
    notification_configured = {
        provider.provider_name: provider.is_configured()
        for provider in notification_providers
    }
    notification_configured.setdefault("email", bool(settings.resend_api_key and settings.owner_email and settings.from_email))
    notification_configured.setdefault("slack", bool(settings.slack_webhook_url))
    notification_configured.setdefault("mock", True)
    selected_notification_provider_names = [provider.provider_name for provider in notification_providers]
    return {
        "lead_sync_provider": lead_sync_provider.provider_name,
        "lead_sync_configured": lead_sync_provider.is_configured(),
        "notification_providers": selected_notification_provider_names,
        "notification_configured": notification_configured,
        "email_optional": True,
        "send_owner_notifications": settings.send_owner_notifications,
        "send_approval_notifications": settings.send_approval_notifications,
        "send_lead_sync_failure_notifications": settings.send_lead_sync_failure_notifications,
        "send_customer_followup_emails": settings.send_customer_followup_emails,
        "lead_sync": {
            "provider": lead_sync_provider.provider_name,
            "configured": lead_sync_provider.is_configured(),
            "automatic": settings.sync_leads_automatically,
            "sync_only_complete_leads": settings.sync_only_complete_leads,
            "google_sheets": {
                "credentials_configured": bool(settings.google_sheets_credentials_json),
                "spreadsheet_configured": bool(settings.google_sheets_spreadsheet_id),
                "worksheet_name": settings.google_sheets_worksheet_name,
            },
        },
        "notification": {
            "provider": ",".join(selected_notification_provider_names),
            "providers": selected_notification_provider_names,
            "configured": all(notification_configured.get(name, False) for name in selected_notification_provider_names),
            "configured_by_provider": notification_configured,
            "email_optional": True,
            "send_owner_notifications": settings.send_owner_notifications,
            "send_approval_notifications": settings.send_approval_notifications,
            "send_lead_sync_failure_notifications": settings.send_lead_sync_failure_notifications,
            "send_customer_followup_emails": settings.send_customer_followup_emails,
        },
        "rag": {
            "provider": settings.rag_provider,
            "vector_dimension": settings.rag_vector_dimension,
            "fallback_to_local": settings.rag_fallback_to_local,
            "embedding_provider": settings.embedding_provider,
            "embedding_model": active_embedding_model_name(),
        },
    }


@router.get("/conversations")
async def get_conversations(request: Request, db: Session = Depends(get_db), limit: int = 25) -> dict:
    require_admin_read(db, request)
    limit = min(max(limit, 1), 100)
    statement = select(Conversation).order_by(Conversation.updated_at.desc()).limit(limit)
    conversations = db.scalars(statement).all()

    return {
        "conversations": [
            _conversation_summary_to_dict(db, conversation)
            for conversation in conversations
        ]
    }


@router.get("/conversations/{conversation_id}/agent-runs")
async def get_conversation_agent_runs(conversation_id: str, request: Request, db: Session = Depends(get_db)) -> dict:
    conversation = db.get(Conversation, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    require_conversation_access(db, request, conversation)

    statement = (
        select(AgentRun)
        .where(AgentRun.conversation_id == conversation_id)
        .order_by(AgentRun.started_at.desc())
    )
    agent_runs = db.scalars(statement).all()
    return {
        "conversation_id": conversation_id,
        "agent_runs": [_agent_run_to_dict(agent_run) for agent_run in agent_runs],
    }


@router.get("/agent-runs")
async def get_agent_runs(request: Request, db: Session = Depends(get_db), limit: int = 25) -> dict:
    require_admin_read(db, request)
    limit = min(max(limit, 1), 100)
    statement = select(AgentRun).order_by(AgentRun.started_at.desc()).limit(limit)
    agent_runs = db.scalars(statement).all()
    return {"agent_runs": [_agent_run_to_dict(agent_run) for agent_run in agent_runs]}


@router.get("/dashboard/summary")
async def get_dashboard_summary(request: Request, db: Session = Depends(get_db)) -> dict:
    require_admin_read(db, request)
    recent_statement = select(AgentRun).order_by(AgentRun.started_at.desc()).limit(5)
    recent_agent_runs = db.scalars(recent_statement).all()

    return {
        "total_conversations": _count_rows(db, Conversation),
        "total_leads": _count_rows(db, Lead),
        "hot_leads": _count_leads_by_quality(db, "hot"),
        "warm_leads": _count_leads_by_quality(db, "warm"),
        "cold_leads": _count_leads_by_quality(db, "cold"),
        "pending_approvals": _count_pending_approvals(db),
        "total_documents": _count_rows(db, Document),
        "total_document_chunks": _count_rows(db, DocumentChunk),
        "recent_agent_runs": [_agent_run_to_dict(agent_run) for agent_run in recent_agent_runs],
    }


@router.post("/documents/ingest-demo")
async def ingest_demo_documents(request: Request, db: Session = Depends(get_db)) -> dict:
    require_admin_write(db, request)
    try:
        result = ingest_documents(db, default_demo_data_dir(), clear_existing=True)
        invalidate_rag_index()
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Document ingestion failed: {exc}") from exc


@router.get("/documents")
async def get_documents(request: Request, db: Session = Depends(get_db)) -> dict:
    require_admin_read(db, request)
    return {"documents": list_documents_with_chunk_counts(db)}


@router.post("/documents/upload")
async def upload_document(upload_request: DocumentUploadRequest, request: Request, db: Session = Depends(get_db)) -> dict:
    require_admin_write(db, request)
    organization = get_or_create_default_organization(db)
    try:
        result = create_document_from_content(
            db,
            title=upload_request.title,
            content=upload_request.content,
            organization_id=organization.id,
        )
        invalidate_rag_index()
        return result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Document upload failed: {exc}") from exc


@router.post("/rag/search")
async def rag_search(rag_request: RagSearchRequest, request: Request, db: Session = Depends(get_db)) -> dict:
    require_admin_read(db, request)
    try:
        return {"query": rag_request.query, "results": search_docs(db, rag_request.query, top_k=rag_request.top_k)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"RAG search failed: {exc}") from exc


@router.get("/approvals")
async def get_approvals(request: Request, db: Session = Depends(get_db)) -> dict:
    require_admin_read(db, request)
    statement = select(HumanApproval).order_by(HumanApproval.created_at.desc())
    approvals = db.scalars(statement).all()
    return {"approvals": [_approval_to_dict(approval) for approval in approvals]}


@router.get("/evals/cases")
async def get_eval_cases(request: Request, db: Session = Depends(get_db)) -> dict:
    require_admin_read(db, request)
    return {"cases": load_eval_cases()}


@router.get("/evals/latest")
async def get_latest_eval_results(request: Request, db: Session = Depends(get_db)) -> dict:
    require_admin_read(db, request)
    return read_latest_eval_results()


@router.post("/evals/run")
async def run_evals(request: Request, db: Session = Depends(get_db)) -> dict:
    settings = get_settings()
    if settings.environment.lower() != "development":
        raise HTTPException(
            status_code=403,
            detail="Eval runs are only allowed when ENVIRONMENT=development.",
        )
    require_admin_write(db, request)
    return run_all_evals(db=db, persist_results=True)


@router.get("/performance/recent")
async def get_recent_performance(request: Request, db: Session = Depends(get_db), limit: int = 25) -> dict:
    require_admin_read(db, request)
    return recent_performance(db, limit=limit)


@router.post("/my/conversations/new")
async def create_my_conversation(request: Request, db: Session = Depends(get_db)) -> dict:
    user = get_current_user_required(request, db)
    organization = get_or_create_default_organization(db)
    conversation = get_or_create_conversation(db, organization_id=organization.id, user_id=user.id)
    return {"conversation": _conversation_summary_to_dict(db, conversation)}


@router.get("/my/conversations")
async def get_my_conversations(request: Request, db: Session = Depends(get_db)) -> dict:
    user = get_current_user_required(request, db)
    statement = select(Conversation).where(Conversation.user_id == user.id).order_by(Conversation.updated_at.desc())
    conversations = db.scalars(statement).all()
    return {"conversations": [_conversation_summary_to_dict(db, conversation) for conversation in conversations]}


@router.get("/my/conversations/{conversation_id}")
async def get_my_conversation(conversation_id: str, request: Request, db: Session = Depends(get_db)) -> dict:
    user = get_current_user_required(request, db)
    conversation = get_conversation_with_messages(db, conversation_id)
    if not conversation or conversation.user_id != user.id:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return _conversation_detail(db, conversation)


@router.get("/guest/conversations")
async def get_guest_conversations(
    db: Session = Depends(get_db),
    x_anonymous_session_token: str | None = Header(default=None, alias="X-Anonymous-Session-Token"),
) -> dict:
    session = get_anonymous_session_by_token(db, x_anonymous_session_token)
    if not session:
        raise HTTPException(status_code=401, detail="Anonymous session token required.")
    statement = (
        select(Conversation)
        .where(Conversation.anonymous_session_id == session.id)
        .order_by(Conversation.updated_at.desc())
    )
    conversations = db.scalars(statement).all()
    return {"conversations": [_conversation_summary_to_dict(db, conversation) for conversation in conversations]}


def _message_to_dict(message: Any) -> dict:
    return {
        "id": message.id,
        "conversation_id": message.conversation_id,
        "role": message.role,
        "content": message.content,
        "created_at": message.created_at.isoformat(),
    }


def _conversation_detail(db: Session, conversation: Conversation) -> dict:
    latest_lead = get_latest_lead_for_conversation(db, conversation.id)
    conversation_data = {
        "id": conversation.id,
        "status": conversation.status,
        "created_at": conversation.created_at.isoformat(),
        "updated_at": conversation.updated_at.isoformat(),
    }
    return {
        **conversation_data,
        "messages": [_message_to_dict(message) for message in conversation.messages],
        "conversation": conversation_data,
        "latest_lead": lead_to_dict(latest_lead),
    }


def _agent_run_to_dict(agent_run: AgentRun) -> dict:
    return {
        "id": agent_run.id,
        "conversation_id": agent_run.conversation_id,
        "user_message": agent_run.user_message,
        "final_response": agent_run.final_response,
        "status": agent_run.status,
        "started_at": agent_run.started_at.isoformat(),
        "finished_at": agent_run.finished_at.isoformat() if agent_run.finished_at else None,
        "total_latency_ms": agent_run.total_latency_ms,
        "total_model_calls": agent_run.total_model_calls,
        "estimated_cost": agent_run.estimated_cost,
        "model_provider": agent_run.model_provider,
        "model_name": agent_run.model_name,
    }


def _conversation_summary_to_dict(db: Session, conversation: Conversation) -> dict:
    latest_message = db.scalars(
        select(Message)
        .where(Message.conversation_id == conversation.id)
        .order_by(Message.created_at.desc())
        .limit(1)
    ).first()
    latest_agent_run = db.scalars(
        select(AgentRun)
        .where(AgentRun.conversation_id == conversation.id)
        .order_by(AgentRun.started_at.desc())
        .limit(1)
    ).first()

    return {
        "id": conversation.id,
        "created_at": conversation.created_at.isoformat(),
        "updated_at": conversation.updated_at.isoformat(),
        "status": conversation.status,
        "last_message": _message_preview(latest_message.content) if latest_message else None,
        "latest_agent_run_id": latest_agent_run.id if latest_agent_run else None,
    }


def _message_preview(content: str, limit: int = 120) -> str:
    normalized = " ".join(content.split())
    if len(normalized) <= limit:
        return normalized
    return f"{normalized[: limit - 1].rstrip()}..."


def _tool_call_to_dict(tool_call: ToolCall) -> dict:
    return {
        "id": tool_call.id,
        "agent_run_id": tool_call.agent_run_id,
        "tool_name": tool_call.tool_name,
        "tool_input": tool_call.tool_input,
        "tool_output": tool_call.tool_output,
        "status": tool_call.status,
        "latency_ms": tool_call.latency_ms,
        "created_at": tool_call.created_at.isoformat(),
    }


def _approval_to_dict(approval: HumanApproval) -> dict:
    return {
        "id": approval.id,
        "agent_run_id": approval.agent_run_id,
        "action_type": approval.action_type,
        "reason": approval.reason,
        "draft_response": approval.draft_response,
        "status": approval.status,
        "created_at": approval.created_at.isoformat(),
        "approved_at": approval.approved_at.isoformat() if approval.approved_at else None,
    }


def _count_rows(db: Session, model: Any) -> int:
    return int(db.scalar(select(func.count()).select_from(model)) or 0)


def _count_leads_by_quality(db: Session, quality: str) -> int:
    return int(db.scalar(select(func.count()).select_from(Lead).where(Lead.lead_quality == quality)) or 0)


def _count_pending_approvals(db: Session) -> int:
    return int(db.scalar(select(func.count()).select_from(HumanApproval).where(HumanApproval.status == "pending")) or 0)


def _require_chat_conversation_access(
    db: Session,
    request: Request,
    conversation: Conversation,
    anonymous_session: AnonymousSession | None,
) -> None:
    settings = get_settings()
    if not settings.auth_enabled:
        return
    user = get_current_user_optional(request, db)
    if user and conversation.user_id == user.id:
        return
    if anonymous_session and conversation.anonymous_session_id == anonymous_session.id:
        return
    organization_id = conversation.organization_id or get_or_create_default_organization(db).id
    if user_has_org_role(db, user, organization_id, ADMIN_READ_ROLES):
        return
    raise HTTPException(status_code=403, detail="You cannot continue this conversation.")


def _can_return_trace(db: Session, user, organization_id: str, auth_enabled: bool) -> bool:
    if not auth_enabled:
        return True
    return user_has_org_role(db, user, organization_id, ADMIN_READ_ROLES)


def _database_connected(db: Session) -> bool:
    try:
        db.execute(select(1))
        return True
    except SQLAlchemyError:
        return False


def _database_kind(database_url: str) -> str:
    if database_url.startswith("sqlite"):
        return "sqlite"
    if database_url.startswith(("postgresql", "postgres")):
        return "postgres"
    return "other"
