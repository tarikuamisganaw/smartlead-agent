from time import perf_counter
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models import AgentRun, AgentTraceEvent, HumanApproval, ToolCall, utc_now
from app.schemas import ChatRequest, ChatResponse, RagSearchRequest
from app.services.conversation_service import add_message, get_conversation_with_messages, get_or_create_conversation
from app.services.document_service import default_demo_data_dir, ingest_documents, list_documents_with_chunk_counts
from app.services.lead_service import get_latest_lead_for_conversation, lead_to_dict, list_leads
from app.services.rag_service import search_docs
from app.services.trace_service import add_trace_event_to_state, now_ms, persist_trace_events
from app.workflow.graph import build_graph
from app.workflow.state import AgentState

router = APIRouter()


@router.get("/health")
async def health() -> dict:
    settings = get_settings()
    return {"status": "ok", "service": settings.service_name}


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
    request_started = perf_counter()
    conversation = get_or_create_conversation(db, request.conversation_id)
    add_message(db, conversation_id=conversation.id, role="user", content=request.message)
    conversation_with_messages = get_conversation_with_messages(db, conversation.id)
    existing_lead = get_latest_lead_for_conversation(db, conversation.id)

    agent_run = AgentRun(
        conversation_id=conversation.id,
        user_message=request.message,
        status="success",
    )
    db.add(agent_run)
    db.commit()
    db.refresh(agent_run)

    initial_state: AgentState = {
        "conversation_id": conversation.id,
        "agent_run_id": agent_run.id,
        "user_message": request.message,
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
    if final_state.get("fatal_error"):
        agent_run.status = "failed"
    elif final_state.get("requires_human_approval"):
        agent_run.status = "pending_approval"
    else:
        agent_run.status = "success"
    db.add(agent_run)
    db.commit()

    add_message(db, conversation_id=conversation.id, role="assistant", content=final_state["final_response"])
    persist_trace_events(db, agent_run.id, final_state.get("trace", []))

    return ChatResponse(
        conversation_id=conversation.id,
        agent_run_id=agent_run.id,
        intent=final_state.get("intent") or "unknown",
        requires_human_approval=bool(final_state.get("requires_human_approval")),
        lead_info={
            **(final_state.get("lead_info") or {}),
            "lead_score": final_state.get("lead_score"),
            "lead_quality": final_state.get("lead_quality"),
        },
        final_response=final_state["final_response"],
        trace=final_state.get("trace", []),
    )


@router.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str, db: Session = Depends(get_db)) -> dict:
    conversation = get_conversation_with_messages(db, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found.")

    latest_lead = get_latest_lead_for_conversation(db, conversation_id)
    conversation_data = {
        "id": conversation.id,
        "status": conversation.status,
        "created_at": conversation.created_at.isoformat(),
        "updated_at": conversation.updated_at.isoformat(),
    }
    messages = [_message_to_dict(message) for message in conversation.messages]

    return {
        **conversation_data,
        "messages": messages,
        "conversation": conversation_data,
        "latest_lead": lead_to_dict(latest_lead),
    }


@router.get("/agent-runs/{agent_run_id}/trace")
async def get_agent_run_trace(agent_run_id: str, db: Session = Depends(get_db)) -> dict:
    agent_run = db.get(AgentRun, agent_run_id)
    if not agent_run:
        raise HTTPException(status_code=404, detail="Agent run not found.")

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
async def get_leads(db: Session = Depends(get_db)) -> dict:
    return {"leads": [lead_to_dict(lead) for lead in list_leads(db)]}


@router.post("/documents/ingest-demo")
async def ingest_demo_documents(db: Session = Depends(get_db)) -> dict:
    try:
        return ingest_documents(db, default_demo_data_dir(), clear_existing=True)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Document ingestion failed: {exc}") from exc


@router.get("/documents")
async def get_documents(db: Session = Depends(get_db)) -> dict:
    return {"documents": list_documents_with_chunk_counts(db)}


@router.post("/rag/search")
async def rag_search(request: RagSearchRequest, db: Session = Depends(get_db)) -> dict:
    try:
        return {"query": request.query, "results": search_docs(db, request.query, top_k=request.top_k)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"RAG search failed: {exc}") from exc


@router.get("/approvals")
async def get_approvals(db: Session = Depends(get_db)) -> dict:
    statement = select(HumanApproval).order_by(HumanApproval.created_at.desc())
    approvals = db.scalars(statement).all()
    return {"approvals": [_approval_to_dict(approval) for approval in approvals]}


def _message_to_dict(message: Any) -> dict:
    return {
        "id": message.id,
        "conversation_id": message.conversation_id,
        "role": message.role,
        "content": message.content,
        "created_at": message.created_at.isoformat(),
    }


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
