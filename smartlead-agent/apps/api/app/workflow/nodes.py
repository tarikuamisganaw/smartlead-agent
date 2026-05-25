from time import perf_counter

from sqlalchemy.orm import Session

from app.models import HumanApproval
from app.services.mock_llm import mock_classify_intent, mock_extract_lead_info, mock_generate_final_response
from app.services.mock_tools import mock_create_lead_record, mock_search_docs, mock_send_owner_notification
from app.services.trace_service import add_trace_event_to_state, now_ms, persist_tool_call
from app.workflow.state import AgentState


AGENT_NAME = "smartlead-agent"


def intent_router_node(state: AgentState) -> AgentState:
    started = perf_counter()
    node_name = "intent_router_node"
    try:
        result = mock_classify_intent(state["user_message"])
        state["intent"] = result.intent
        state["intent_confidence"] = result.confidence
        state["needs_rag"] = result.needs_rag
        state["requires_human_approval"] = result.requires_human_approval
        if result.requires_human_approval:
            state["approval_reason"] = result.reason
        add_trace_event_to_state(
            state,
            agent_name=AGENT_NAME,
            node_name=node_name,
            input_summary=_short(state["user_message"]),
            output_summary=f"intent={result.intent}, confidence={result.confidence}, needs_rag={result.needs_rag}",
            status="success",
            latency_ms=now_ms(started),
        )
    except Exception as exc:  # pragma: no cover - defensive path
        _record_node_failure(state, node_name, exc, started)
    return state


def rag_node(state: AgentState) -> AgentState:
    started = perf_counter()
    node_name = "rag_node"
    try:
        if not state.get("needs_rag"):
            add_trace_event_to_state(
                state,
                agent_name=AGENT_NAME,
                node_name=node_name,
                input_summary="needs_rag=false",
                output_summary="Skipped document lookup.",
                status="skipped",
                latency_ms=now_ms(started),
            )
            return state

        docs = mock_search_docs(state["user_message"])
        state["retrieved_docs"] = docs
        add_trace_event_to_state(
            state,
            agent_name=AGENT_NAME,
            node_name=node_name,
            input_summary=_short(state["user_message"]),
            output_summary=f"Retrieved {len(docs)} mock document(s).",
            tool_name="mock_search_docs",
            status="success",
            latency_ms=now_ms(started),
        )
    except Exception as exc:  # pragma: no cover - defensive path
        _record_node_failure(state, node_name, exc, started)
    return state


def lead_qualification_node(state: AgentState) -> AgentState:
    started = perf_counter()
    node_name = "lead_qualification_node"
    try:
        if not _should_extract_lead_info(state):
            add_trace_event_to_state(
                state,
                agent_name=AGENT_NAME,
                node_name=node_name,
                input_summary=f"intent={state.get('intent')}",
                output_summary="Skipped lead extraction.",
                status="skipped",
                latency_ms=now_ms(started),
            )
            return state

        lead_info = mock_extract_lead_info(state["user_message"])
        state["lead_info"] = lead_info.model_dump()
        state["missing_lead_fields"] = lead_info.missing_fields
        add_trace_event_to_state(
            state,
            agent_name=AGENT_NAME,
            node_name=node_name,
            input_summary=_short(state["user_message"]),
            output_summary=(
                f"service_interest={lead_info.service_interest}, budget={lead_info.budget}, "
                f"missing={lead_info.missing_fields}"
            ),
            status="success",
            latency_ms=now_ms(started),
        )
    except Exception as exc:  # pragma: no cover - defensive path
        _record_node_failure(state, node_name, exc, started)
    return state


def lead_scoring_node(state: AgentState) -> AgentState:
    started = perf_counter()
    node_name = "lead_scoring_node"
    try:
        lead_info = state.get("lead_info") or {}
        score = 0
        if lead_info.get("budget") is not None:
            score += 30
        if _has_soon_timeline(lead_info.get("timeline")):
            score += 25
        if lead_info.get("service_interest"):
            score += 25
        if lead_info.get("email"):
            score += 20

        state["lead_score"] = min(score, 100)
        state["lead_quality"] = _quality_for_score(state["lead_score"])
        add_trace_event_to_state(
            state,
            agent_name=AGENT_NAME,
            node_name=node_name,
            input_summary=f"lead_info_keys={sorted(key for key, value in lead_info.items() if value)}",
            output_summary=f"score={state['lead_score']}, quality={state['lead_quality']}",
            status="success",
            latency_ms=now_ms(started),
        )
    except Exception as exc:  # pragma: no cover - defensive path
        _record_node_failure(state, node_name, exc, started)
    return state


def safety_node(state: AgentState) -> AgentState:
    started = perf_counter()
    node_name = "safety_node"
    try:
        lowered = state["user_message"].lower()
        risky_keywords = ("discount", "refund", "guarantee", "promise results")
        if state.get("intent") == "discount_request" or any(keyword in lowered for keyword in risky_keywords):
            state["requires_human_approval"] = True
            state["approval_reason"] = "Request involves discount, refund, guarantee, or promised results."
            output = "Human approval required."
        else:
            state["requires_human_approval"] = False
            state["approval_reason"] = None
            output = "No risky action detected."

        add_trace_event_to_state(
            state,
            agent_name=AGENT_NAME,
            node_name=node_name,
            input_summary=f"intent={state.get('intent')}",
            output_summary=output,
            status="success",
            latency_ms=now_ms(started),
        )
    except Exception as exc:  # pragma: no cover - defensive path
        _record_node_failure(state, node_name, exc, started)
    return state


def action_node(state: AgentState, db: Session) -> AgentState:
    started = perf_counter()
    node_name = "action_node"
    try:
        if state.get("requires_human_approval"):
            approval = HumanApproval(
                agent_run_id=state["agent_run_id"],
                action_type="review_special_request",
                reason=state.get("approval_reason") or "Human review required.",
                draft_response="Special requests require team review before approval.",
            )
            db.add(approval)
            db.commit()
            db.refresh(approval)
            state["selected_action"] = "human_approval"
            state["tool_results"].append(
                {
                    "tool_name": "create_human_approval",
                    "status": "pending",
                    "human_approval_id": approval.id,
                }
            )
            add_trace_event_to_state(
                state,
                agent_name=AGENT_NAME,
                node_name=node_name,
                input_summary="requires_human_approval=true",
                output_summary=f"Created pending HumanApproval {approval.id}.",
                status="success",
                latency_ms=now_ms(started),
            )
            return state

        lead_info = state.get("lead_info") or {}
        if not _has_enough_lead_data(lead_info):
            state["selected_action"] = "none"
            add_trace_event_to_state(
                state,
                agent_name=AGENT_NAME,
                node_name=node_name,
                input_summary="lead_info did not meet save threshold",
                output_summary="No lead or notification created.",
                status="skipped",
                latency_ms=now_ms(started),
            )
            return state

        lead_started = perf_counter()
        lead = mock_create_lead_record(
            db=db,
            conversation_id=state["conversation_id"],
            lead_info=lead_info,
            lead_score=state.get("lead_score"),
            lead_quality=state.get("lead_quality"),
        )
        lead_latency = now_ms(lead_started)
        persist_tool_call(
            db,
            agent_run_id=state["agent_run_id"],
            tool_name="mock_create_lead_record",
            tool_input={"conversation_id": state["conversation_id"], "lead_info": lead_info},
            tool_output={"lead_id": lead.id, "lead_quality": lead.lead_quality},
            status="success",
            latency_ms=lead_latency,
        )

        notify_started = perf_counter()
        notification = mock_send_owner_notification(lead_info)
        notify_latency = now_ms(notify_started)
        persist_tool_call(
            db,
            agent_run_id=state["agent_run_id"],
            tool_name="mock_send_owner_notification",
            tool_input=lead_info,
            tool_output=notification,
            status="success",
            latency_ms=notify_latency,
        )

        state["selected_action"] = "create_lead_and_notify_owner"
        state["tool_results"].extend(
            [
                {"tool_name": "mock_create_lead_record", "status": "success", "lead_id": lead.id},
                {"tool_name": "mock_send_owner_notification", "status": "success", "result": notification},
            ]
        )
        add_trace_event_to_state(
            state,
            agent_name=AGENT_NAME,
            node_name=node_name,
            input_summary="lead save threshold met",
            output_summary=f"Created lead {lead.id} and mock owner notification.",
            status="success",
            latency_ms=now_ms(started),
        )
    except Exception as exc:  # pragma: no cover - defensive path
        db.rollback()
        _record_node_failure(state, node_name, exc, started)
    return state


def final_response_node(state: AgentState) -> AgentState:
    started = perf_counter()
    node_name = "final_response_node"
    try:
        if state.get("errors"):
            state["final_response"] = "Sorry, something went wrong while processing that request. The team can review it."
            status = "failed"
        else:
            final = mock_generate_final_response(state)
            state["final_response"] = final.message
            status = "success"

        add_trace_event_to_state(
            state,
            agent_name=AGENT_NAME,
            node_name=node_name,
            input_summary=f"intent={state.get('intent')}",
            output_summary=_short(state["final_response"] or ""),
            status=status,
            latency_ms=now_ms(started),
        )
    except Exception as exc:  # pragma: no cover - defensive path
        _record_node_failure(state, node_name, exc, started)
        state["final_response"] = "Sorry, something went wrong while preparing the response."
    return state


def _should_extract_lead_info(state: AgentState) -> bool:
    intent = state.get("intent")
    if intent == "lead_inquiry":
        return True
    if intent == "pricing_question":
        lowered = state["user_message"].lower()
        return any(keyword in lowered for keyword in ("seo", "website", "ads", "marketing", "automation", "budget", "$"))
    return False


def _has_soon_timeline(timeline: str | None) -> bool:
    if not timeline:
        return False
    return timeline.lower() in {"today", "this week", "next week", "next month", "asap"}


def _quality_for_score(score: int) -> str:
    if score <= 39:
        return "cold"
    if score <= 69:
        return "warm"
    return "hot"


def _has_enough_lead_data(lead_info: dict) -> bool:
    return bool(lead_info.get("service_interest") or lead_info.get("budget"))


def _record_node_failure(state: AgentState, node_name: str, exc: Exception, started: float) -> None:
    error = {"node_name": node_name, "error": str(exc)}
    state.setdefault("errors", []).append(error)
    add_trace_event_to_state(
        state,
        agent_name=AGENT_NAME,
        node_name=node_name,
        input_summary=None,
        output_summary=None,
        status="failed",
        error_message=str(exc),
        latency_ms=now_ms(started),
    )


def _short(value: str, limit: int = 160) -> str:
    return value if len(value) <= limit else f"{value[:limit]}..."
