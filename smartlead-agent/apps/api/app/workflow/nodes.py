from time import perf_counter

from sqlalchemy.orm import Session

from app.models import HumanApproval
from app.services.mock_tools import create_followup_draft, create_or_update_lead_record, mock_send_owner_notification
from app.services.lead_service import merge_lead_info, score_lead_info
from app.services.llm_service import (
    LLMCallResult,
    classify_intent_with_metadata,
    extract_lead_info_with_metadata,
    generate_final_response_with_metadata,
)
from app.services.metrics_service import record_model_call
from app.services.rag_service import search_docs
from app.services.trace_service import add_trace_event_to_state, now_ms, persist_tool_call
from app.workflow.state import AgentState


AGENT_NAME = "smartlead-agent"


def intent_router_node(state: AgentState) -> AgentState:
    started = perf_counter()
    node_name = "intent_router_node"
    try:
        llm_result = classify_intent_with_metadata(state["user_message"], _conversation_context(state))
        _record_llm_metrics(state, llm_result)
        result = llm_result.value
        state["intent"] = result.intent
        state["intent_confidence"] = result.confidence
        state["needs_rag"] = result.needs_rag
        state["requires_human_approval"] = result.requires_human_approval
        if state["intent"] == "unknown" and (state.get("existing_lead") or _message_has_lead_fields(state["user_message"])):
            state["intent"] = "lead_inquiry"
            state["intent_confidence"] = 0.76
            state["needs_rag"] = False
        if result.requires_human_approval:
            state["approval_reason"] = result.reason
        add_trace_event_to_state(
            state,
            agent_name=AGENT_NAME,
            node_name=node_name,
            input_summary=_short(state["user_message"]),
            output_summary=(
                f"Classified intent as {state['intent']} using provider={llm_result.provider} "
                f"model={llm_result.model}; confidence={state['intent_confidence']}; "
                f"needs_rag={state['needs_rag']}; fallback_used={llm_result.fallback_used}"
                f"{_trace_error_suffix(llm_result.error_message)}"
            ),
            status="success",
            latency_ms=now_ms(started),
        )
    except Exception as exc:  # pragma: no cover - defensive path
        _record_node_failure(state, node_name, exc, started)
    return state


def rag_node(state: AgentState, db: Session) -> AgentState:
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

        query = f"{state['user_message']} intent:{state.get('intent') or 'unknown'}"
        docs = search_docs(db, query, top_k=4)
        state["retrieved_docs"] = docs
        persist_tool_call(
            db,
            agent_run_id=state["agent_run_id"],
            tool_name="search_docs",
            tool_input={"query": query, "top_k": 4},
            tool_output=[
                {
                    "chunk_id": doc.get("chunk_id"),
                    "title": doc.get("title"),
                    "score": doc.get("score"),
                }
                for doc in docs
            ],
            status="success",
            latency_ms=now_ms(started),
        )
        titles = ", ".join(dict.fromkeys(doc.get("title", "unknown") for doc in docs))
        add_trace_event_to_state(
            state,
            agent_name="RAG Agent",
            node_name=node_name,
            input_summary=_short(state["user_message"]),
            output_summary=f"Retrieved {len(docs)} document chunks: {titles or 'none'}",
            tool_name="search_docs",
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

        llm_result = extract_lead_info_with_metadata(state["user_message"], _conversation_context(state))
        _record_llm_metrics(state, llm_result)
        lead_info = llm_result.value
        merged_info = merge_lead_info(state.get("existing_lead"), lead_info.model_dump())
        state["lead_info"] = merged_info
        state["missing_lead_fields"] = merged_info.get("missing_fields", [])
        add_trace_event_to_state(
            state,
            agent_name=AGENT_NAME,
            node_name=node_name,
            input_summary=_short(state["user_message"]),
            output_summary=(
                f"service_interest={merged_info.get('service_interest')}, budget={merged_info.get('budget')}, "
                f"missing={merged_info.get('missing_fields', [])}; provider={llm_result.provider} "
                f"model={llm_result.model}; fallback_used={llm_result.fallback_used}"
                f"{_trace_error_suffix(llm_result.error_message)}"
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
        state["lead_score"], state["lead_quality"] = score_lead_info(lead_info)
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
        risky_keywords = ("discount", "refund", "guarantee", "promise results", "can you guarantee", "70% off", "free service")
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
        lead_info = state.get("lead_info") or {}
        lead = None
        if _should_save_lead(state, lead_info):
            lead_started = perf_counter()
            lead = create_or_update_lead_record(
                db=db,
                conversation_id=state["conversation_id"],
                lead_info=lead_info,
                lead_score=state.get("lead_score"),
                lead_quality=state.get("lead_quality"),
                organization_id=state.get("organization_id"),
                user_id=state.get("user_id"),
                anonymous_session_id=state.get("anonymous_session_id"),
            )
            lead_latency = now_ms(lead_started)
            lead_info["id"] = lead.id
            lead_info["lead_score"] = lead.lead_score
            lead_info["lead_quality"] = lead.lead_quality
            state["lead_info"] = lead_info
            state["existing_lead"] = {
                **lead_info,
                "conversation_id": lead.conversation_id,
                "status": lead.status,
            }
            persist_tool_call(
                db,
                agent_run_id=state["agent_run_id"],
                tool_name="create_or_update_lead_record",
                tool_input={"conversation_id": state["conversation_id"], "lead_info": lead_info},
                tool_output={"lead_id": lead.id, "lead_quality": lead.lead_quality},
                status="success",
                latency_ms=lead_latency,
            )
            state["tool_results"].append(
                {"tool_name": "create_or_update_lead_record", "status": "success", "lead_id": lead.id}
            )

        if state.get("requires_human_approval"):
            action_type = _approval_action_type(state["user_message"])
            approval = HumanApproval(
                agent_run_id=state["agent_run_id"],
                organization_id=state.get("organization_id"),
                action_type=action_type,
                reason=state.get("approval_reason") or "Human review required.",
                draft_response="Special requests require team review before approval.",
            )
            db.add(approval)
            db.commit()
            db.refresh(approval)
            persist_tool_call(
                db,
                agent_run_id=state["agent_run_id"],
                tool_name="create_human_approval",
                tool_input={"action_type": action_type, "reason": approval.reason},
                tool_output={"human_approval_id": approval.id, "status": approval.status},
                status="success",
                latency_ms=now_ms(started),
            )
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

        if not lead:
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

        followup_started = perf_counter()
        followup = create_followup_draft(lead_info, state.get("retrieved_docs") or [])
        persist_tool_call(
            db,
            agent_run_id=state["agent_run_id"],
            tool_name="create_followup_draft",
            tool_input={"lead_info": lead_info, "retrieved_doc_count": len(state.get("retrieved_docs") or [])},
            tool_output=followup,
            status="success",
            latency_ms=now_ms(followup_started),
        )

        notification = None
        if lead.email and lead.service_interest:
            notify_started = perf_counter()
            notification = mock_send_owner_notification(lead_info)
            persist_tool_call(
                db,
                agent_run_id=state["agent_run_id"],
                tool_name="mock_send_owner_notification",
                tool_input=lead_info,
                tool_output=notification,
                status="success",
                latency_ms=now_ms(notify_started),
            )

        state["selected_action"] = "create_or_update_lead"
        state["tool_results"].extend(
            [
                {"tool_name": "create_followup_draft", "status": "success", "result": followup},
            ]
        )
        if notification:
            state["selected_action"] = "create_or_update_lead_and_notify_owner"
            state["tool_results"].append(
                {"tool_name": "mock_send_owner_notification", "status": "success", "result": notification}
            )
        add_trace_event_to_state(
            state,
            agent_name=AGENT_NAME,
            node_name=node_name,
            input_summary="lead save threshold met",
            output_summary=f"Saved lead {lead.id}; notification_sent={bool(notification)}.",
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
        if state.get("fatal_error"):
            state["final_response"] = "Sorry, something went wrong while processing that request. The team can review it."
            status = "failed"
        else:
            llm_result = generate_final_response_with_metadata(state)
            _record_llm_metrics(state, llm_result)
            final = llm_result.value
            state["final_response"] = final.message
            status = "success"
            provider_summary = (
                f"; provider={llm_result.provider} model={llm_result.model}; "
                f"fallback_used={llm_result.fallback_used}{_trace_error_suffix(llm_result.error_message)}"
            )

        add_trace_event_to_state(
            state,
            agent_name=AGENT_NAME,
            node_name=node_name,
            input_summary=f"intent={state.get('intent')}",
            output_summary=_short(f"{state['final_response'] or ''}{provider_summary if status == 'success' else ''}"),
            status=status,
            latency_ms=now_ms(started),
        )
    except Exception as exc:  # pragma: no cover - defensive path
        _record_node_failure(state, node_name, exc, started)
        state["final_response"] = "Sorry, something went wrong while preparing the response."
    return state


def _should_extract_lead_info(state: AgentState) -> bool:
    intent = state.get("intent")
    if state.get("existing_lead"):
        return True
    if intent == "lead_inquiry":
        return True
    if intent == "pricing_question":
        lowered = state["user_message"].lower()
        return any(keyword in lowered for keyword in ("budget", "$", "email", "phone", "my name is", "i am", "i'm"))
    if _message_has_lead_fields(state["user_message"]):
        return True
    return False


def _message_has_lead_fields(message: str) -> bool:
    lowered = message.lower()
    return bool(
        "@" in message
        or "$" in message
        or any(keyword in lowered for keyword in ("my name is", "i am", "i'm", "budget", "phone", "email"))
    )


def _has_meaningful_lead_data(lead_info: dict) -> bool:
    return any(
        lead_info.get(field)
        for field in ("service_interest", "budget", "email", "phone", "business_type", "timeline")
    )


def _should_save_lead(state: AgentState, lead_info: dict) -> bool:
    if not _has_meaningful_lead_data(lead_info):
        return False
    if state.get("existing_lead") or state.get("intent") == "lead_inquiry":
        return True
    return any(lead_info.get(field) for field in ("budget", "email", "phone", "business_type", "timeline"))


def _approval_action_type(message: str) -> str:
    lowered = message.lower()
    if "refund" in lowered:
        return "refund_request"
    if any(keyword in lowered for keyword in ("discount", "off", "free service")):
        return "discount_request"
    if any(keyword in lowered for keyword in ("guarantee", "promise results", "can you guarantee")):
        return "guarantee_request"
    return "risky_request"


def _conversation_context(state: AgentState) -> str:
    parts = []
    existing_lead = state.get("existing_lead")
    if existing_lead:
        parts.append(f"Existing lead: {existing_lead}")
    for message in (state.get("conversation_history") or [])[-6:]:
        parts.append(f"{message.get('role')}: {message.get('content')}")
    return "\n".join(parts)


def _trace_error_suffix(error_message: str | None) -> str:
    if not error_message:
        return ""
    return f"; fallback_error={_short(error_message, 120)}"


def _record_llm_metrics(state: AgentState, llm_result: LLMCallResult) -> None:
    record_model_call(state, provider=llm_result.provider, model=llm_result.model)


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
