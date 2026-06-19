import json
from pathlib import Path
from time import perf_counter
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import SessionLocal, init_db
from app.models import AgentRun, Conversation, DocumentChunk, Lead, ToolCall, utc_now
from app.services.conversation_service import add_message, get_conversation_with_messages
from app.services.document_service import default_demo_data_dir, ingest_documents
from app.services.auth_service import get_or_create_default_organization
from app.services.lead_service import get_latest_lead_for_conversation, lead_to_dict
from app.services.metrics_service import collect_agent_run_metrics, default_model_metadata
from app.services.trace_service import add_trace_event_to_state, now_ms, persist_trace_events
from app.workflow.graph import build_graph
from app.workflow.state import AgentState

EVAL_CASES_PATH = Path(__file__).resolve().parent / "eval_cases.json"
EVAL_RESULTS_DIR = Path(__file__).resolve().parents[2] / "eval_results"
LATEST_RESULTS_PATH = EVAL_RESULTS_DIR / "latest_eval_results.json"


def load_eval_cases(path: Path | None = None) -> list[dict]:
    cases_path = path or EVAL_CASES_PATH
    return json.loads(cases_path.read_text(encoding="utf-8"))


def run_all_evals(db: Session | None = None, *, persist_results: bool = True) -> dict:
    init_db()
    owns_session = db is None
    session = db or SessionLocal()
    try:
        _ensure_documents(session)
        cases = load_eval_cases()
        results = [run_single_eval_case(case, session) for case in cases]
        summary = _summarize_results(results)
        payload = {
            "provider": get_settings().model_provider,
            "model": _configured_model_name(),
            "total_cases": summary["total_cases"],
            "passed_cases": summary["passed_cases"],
            "pass_rate": summary["pass_rate"],
            "metrics": summary["metrics"],
            "results": results,
        }
        if persist_results:
            write_latest_eval_results(payload)
        return payload
    finally:
        if owns_session:
            session.close()


def run_single_eval_case(case: dict, db: Session) -> dict:
    started = perf_counter()
    errors: list[str] = []
    organization = get_or_create_default_organization(db)
    conversation = Conversation(status="eval", organization_id=organization.id)
    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    turn_inputs = case.get("turns") or [case.get("input", "")]
    actual_response: dict[str, Any] | None = None

    try:
        for message in turn_inputs:
            actual_response = _run_eval_turn(db, conversation.id, message)
    except Exception as exc:  # pragma: no cover - defensive eval runner path.
        db.rollback()
        errors.append(str(exc))

    latest_lead = get_latest_lead_for_conversation(db, conversation.id)
    lead_count = int(
        db.scalar(select(func.count()).select_from(Lead).where(Lead.conversation_id == conversation.id)) or 0
    )
    db_state = {
        "conversation_id": conversation.id,
        "latest_lead": lead_to_dict(latest_lead),
        "lead_count": lead_count,
    }
    scored = score_eval_result(case, actual_response or {}, db_state)
    errors.extend(scored["errors"])

    return {
        "case_id": case["id"],
        "passed": scored["passed"] and not errors,
        "scores": scored["scores"],
        "expected": _expected_snapshot(case),
        "actual": {
            **(actual_response or {}),
            "latest_lead": db_state["latest_lead"],
            "lead_count": lead_count,
        },
        "errors": errors,
        "latency_ms": now_ms(started),
    }


def score_eval_result(case: dict, actual_response: dict, db_state: dict) -> dict:
    errors: list[str] = []
    actual_sources = {doc.get("title") for doc in actual_response.get("retrieved_docs", [])}
    tool_names = {tool.get("tool_name") for tool in actual_response.get("tool_results", [])}
    final_lead = db_state.get("latest_lead") or actual_response.get("lead_info") or {}

    scores = {
        "intent_correct": _score_expected(case, actual_response, "expected_intent", "intent"),
        "rag_usage_correct": _score_rag(case, actual_response, actual_sources),
        "lead_extraction_correct": _score_lead_extraction(case, final_lead, db_state),
        "approval_correct": _score_expected(case, actual_response, "expected_human_approval", "requires_human_approval"),
        "tool_call_correct": _score_tool_calls(case, tool_names, db_state),
        "valid_output": bool(actual_response.get("final_response")),
    }

    _append_score_errors(case["id"], scores, errors)
    return {"passed": all(scores.values()), "scores": scores, "errors": errors}


def write_latest_eval_results(results: dict) -> None:
    EVAL_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    LATEST_RESULTS_PATH.write_text(json.dumps(results, indent=2), encoding="utf-8")


def read_latest_eval_results() -> dict:
    if not LATEST_RESULTS_PATH.exists():
        return {
            "status": "missing",
            "message": "No eval results found yet. Run POST /evals/run or python -m app.evals.run_evals.",
            "results": None,
        }
    return json.loads(LATEST_RESULTS_PATH.read_text(encoding="utf-8"))


def _run_eval_turn(db: Session, conversation_id: str, message: str) -> dict:
    request_started = perf_counter()
    add_message(db, conversation_id=conversation_id, role="user", content=message)
    conversation = get_conversation_with_messages(db, conversation_id)
    existing_lead = get_latest_lead_for_conversation(db, conversation_id)
    organization = get_or_create_default_organization(db)
    model_provider, model_name = default_model_metadata()

    agent_run = AgentRun(
        conversation_id=conversation_id,
        organization_id=organization.id,
        user_message=message,
        status="success",
        model_provider=model_provider,
        model_name=model_name,
    )
    db.add(agent_run)
    db.commit()
    db.refresh(agent_run)

    initial_state: AgentState = {
        "conversation_id": conversation_id,
        "agent_run_id": agent_run.id,
        "user_message": message,
        "organization_id": organization.id,
        "user_id": None,
        "anonymous_session_id": None,
        "conversation_history": [
            {"role": row.role, "content": row.content, "created_at": row.created_at.isoformat()}
            for row in (conversation.messages if conversation else [])
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
        final_state = build_graph(db).invoke(initial_state)
    except Exception as exc:  # pragma: no cover - defensive eval fallback.
        db.rollback()
        final_state = initial_state
        final_state["errors"].append({"node_name": "workflow", "error": str(exc)})
        final_state["fatal_error"] = True
        final_state["final_response"] = "Sorry, something went wrong while processing that request."
        add_trace_event_to_state(
            final_state,
            agent_name="smartlead-agent",
            node_name="workflow",
            input_summary="Eval workflow invocation failed.",
            output_summary="Returned safe fallback response.",
            status="failed",
            error_message=str(exc),
            latency_ms=now_ms(request_started),
        )

    if not final_state.get("final_response"):
        final_state["final_response"] = "Sorry, I could not produce a response for that request."

    metrics = collect_agent_run_metrics(final_state)
    agent_run.final_response = final_state["final_response"]
    agent_run.finished_at = utc_now()
    agent_run.total_latency_ms = now_ms(request_started)
    agent_run.total_model_calls = metrics["total_model_calls"]
    agent_run.estimated_cost = metrics["estimated_cost"]
    agent_run.model_provider = metrics["model_provider"]
    agent_run.model_name = metrics["model_name"]
    agent_run.status = "failed" if final_state.get("fatal_error") else "pending_approval" if final_state.get("requires_human_approval") else "success"
    db.add(agent_run)
    db.commit()

    add_message(db, conversation_id=conversation_id, role="assistant", content=final_state["final_response"])
    persist_trace_events(db, agent_run.id, final_state.get("trace", []))

    tool_calls = list(db.scalars(select(ToolCall).where(ToolCall.agent_run_id == agent_run.id)).all())

    return {
        "conversation_id": conversation_id,
        "agent_run_id": agent_run.id,
        "intent": final_state.get("intent") or "unknown",
        "needs_rag": bool(final_state.get("needs_rag")),
        "retrieved_docs": final_state.get("retrieved_docs", []),
        "lead_info": final_state.get("lead_info") or {},
        "requires_human_approval": bool(final_state.get("requires_human_approval")),
        "selected_action": final_state.get("selected_action"),
        "tool_results": [
            {"tool_name": tool.tool_name, "status": tool.status}
            for tool in tool_calls
        ],
        "final_response": final_state["final_response"],
        "trace": final_state.get("trace", []),
        "total_model_calls": agent_run.total_model_calls,
        "estimated_cost": agent_run.estimated_cost,
        "model_provider": agent_run.model_provider,
        "model_name": agent_run.model_name,
        "latency_ms": agent_run.total_latency_ms,
    }


def _ensure_documents(db: Session) -> None:
    chunk_count = int(db.scalar(select(func.count()).select_from(DocumentChunk)) or 0)
    if chunk_count == 0:
        ingest_documents(db, default_demo_data_dir(), clear_existing=True)


def _score_expected(case: dict, actual_response: dict, expected_key: str, actual_key: str) -> bool:
    if expected_key not in case:
        return True
    return actual_response.get(actual_key) == case.get(expected_key)


def _score_rag(case: dict, actual_response: dict, actual_sources: set[str | None]) -> bool:
    expected_needs_rag = case.get("expected_needs_rag")
    if expected_needs_rag is not None and actual_response.get("needs_rag") != expected_needs_rag:
        return False

    expected_sources = case.get("expected_sources") or []
    if expected_sources:
        return all(any(source in (actual_source or "") for actual_source in actual_sources) for source in expected_sources)
    return True


def _score_lead_extraction(case: dict, final_lead: dict, db_state: dict) -> bool:
    expected_fields = {
        "service_interest": case.get("expected_service_interest"),
        "business_type": case.get("expected_business_type"),
        "budget": case.get("expected_budget"),
        **(case.get("expected_final_lead") or {}),
    }
    expected_fields = {key: value for key, value in expected_fields.items() if value is not None}
    if expected_fields and not all(final_lead.get(key) == value for key, value in expected_fields.items()):
        return False

    if case.get("should_create_lead") is True and db_state.get("lead_count", 0) < 1:
        return False
    if case.get("should_create_lead") is False and db_state.get("lead_count", 0) > 0:
        return False
    if case.get("should_create_duplicate_leads") is False and db_state.get("lead_count", 0) > 1:
        return False
    return True


def _score_tool_calls(case: dict, tool_names: set[str | None], db_state: dict) -> bool:
    if case.get("expected_needs_rag") and "search_docs" not in tool_names:
        return False
    if case.get("should_create_lead") and "create_or_update_lead_record" not in tool_names:
        return False
    if case.get("expected_human_approval") and "create_human_approval" not in tool_names:
        return False
    if case.get("should_create_duplicate_leads") is False and db_state.get("lead_count", 0) > 1:
        return False
    return True


def _append_score_errors(case_id: str, scores: dict[str, bool], errors: list[str]) -> None:
    for name, passed in scores.items():
        if not passed:
            errors.append(f"{case_id}: {name} failed")


def _summarize_results(results: list[dict]) -> dict:
    total_cases = len(results)
    passed_cases = sum(1 for result in results if result["passed"])
    score_names = [
        "intent_correct",
        "rag_usage_correct",
        "lead_extraction_correct",
        "approval_correct",
        "tool_call_correct",
        "valid_output",
    ]
    metrics = {
        name: _accuracy(results, name)
        for name in score_names
    }
    metrics["average_latency_ms"] = round(
        sum(result.get("latency_ms") or 0 for result in results) / total_cases if total_cases else 0,
        2,
    )
    metrics["estimated_cost"] = round(
        sum(float((result.get("actual") or {}).get("estimated_cost") or 0) for result in results),
        8,
    )

    return {
        "total_cases": total_cases,
        "passed_cases": passed_cases,
        "pass_rate": round(passed_cases / total_cases, 4) if total_cases else 0,
        "metrics": metrics,
    }


def _accuracy(results: list[dict], score_name: str) -> float:
    if not results:
        return 0.0
    return round(sum(1 for result in results if result["scores"].get(score_name)) / len(results), 4)


def _expected_snapshot(case: dict) -> dict:
    return {
        key: value
        for key, value in case.items()
        if key != "turns" and key != "input"
    }


def _configured_model_name() -> str | None:
    provider = get_settings().model_provider.lower().strip()
    if provider == "gemini":
        return get_settings().gemini_model
    return "mock-rules-v1"
