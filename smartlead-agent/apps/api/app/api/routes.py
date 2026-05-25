from time import perf_counter

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models import AgentRun, AgentTraceEvent, utc_now
from app.schemas import ChatRequest, ChatResponse
from app.services.conversation_service import add_message, get_conversation_with_messages, get_or_create_conversation
from app.services.lead_service import list_leads
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
    }

    try:
        graph = build_graph(db)
        final_state = graph.invoke(initial_state)
    except Exception as exc:  # pragma: no cover - defensive route fallback
        db.rollback()
        final_state = initial_state
        final_state["errors"].append({"node_name": "workflow", "error": str(exc)})
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
    if final_state.get("errors"):
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

    return {
        "id": conversation.id,
        "status": conversation.status,
        "created_at": conversation.created_at.isoformat(),
        "updated_at": conversation.updated_at.isoformat(),
        "messages": [
            {
                "id": message.id,
                "conversation_id": message.conversation_id,
                "role": message.role,
                "content": message.content,
                "created_at": message.created_at.isoformat(),
            }
            for message in conversation.messages
        ],
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
    }


@router.get("/leads")
async def get_leads(db: Session = Depends(get_db)) -> dict:
    return {
        "leads": [
            {
                "id": lead.id,
                "conversation_id": lead.conversation_id,
                "name": lead.name,
                "email": lead.email,
                "phone": lead.phone,
                "business_type": lead.business_type,
                "service_interest": lead.service_interest,
                "budget": lead.budget,
                "timeline": lead.timeline,
                "lead_score": lead.lead_score,
                "lead_quality": lead.lead_quality,
                "status": lead.status,
                "created_at": lead.created_at.isoformat(),
            }
            for lead in list_leads(db)
        ]
    }
