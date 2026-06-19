from time import perf_counter
from typing import Any

from sqlalchemy.orm import Session

from app.models import AgentTraceEvent, ToolCall


def now_ms(start: float) -> int:
    return int((perf_counter() - start) * 1000)


def add_trace_event_to_state(
    state: dict,
    *,
    agent_name: str,
    node_name: str,
    input_summary: str | None = None,
    output_summary: str | None = None,
    tool_name: str | None = None,
    status: str = "success",
    error_message: str | None = None,
    latency_ms: int | None = None,
) -> dict:
    trace = state.setdefault("trace", [])
    event = {
        "step_number": len(trace) + 1,
        "agent_name": agent_name,
        "node_name": node_name,
        "input_summary": input_summary,
        "output_summary": output_summary,
        "tool_name": tool_name,
        "status": status,
        "error_message": error_message,
        "latency_ms": latency_ms,
    }
    trace.append(event)
    return event


def persist_trace_events(db: Session, agent_run_id: str, trace: list[dict[str, Any]]) -> list[AgentTraceEvent]:
    events = [
        AgentTraceEvent(
            agent_run_id=agent_run_id,
            step_number=event.get("step_number", index + 1),
            agent_name=event.get("agent_name", "smartlead-agent"),
            node_name=event.get("node_name", "unknown"),
            input_summary=event.get("input_summary"),
            output_summary=event.get("output_summary"),
            tool_name=event.get("tool_name"),
            status=event.get("status", "success"),
            error_message=event.get("error_message"),
            latency_ms=event.get("latency_ms"),
        )
        for index, event in enumerate(trace)
    ]
    db.add_all(events)
    db.commit()
    return events


def persist_tool_call(
    db: Session,
    *,
    agent_run_id: str,
    tool_name: str,
    tool_input: dict | list | str | None,
    tool_output: dict | list | str | None,
    status: str = "success",
    latency_ms: int | None = None,
) -> ToolCall:
    tool_call = ToolCall(
        agent_run_id=agent_run_id,
        tool_name=tool_name,
        tool_input=tool_input,
        tool_output=tool_output,
        status=status,
        latency_ms=latency_ms,
    )
    db.add(tool_call)
    db.commit()
    db.refresh(tool_call)
    return tool_call
