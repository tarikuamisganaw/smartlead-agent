from statistics import mean

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AgentRun, AgentTraceEvent


def recent_performance(db: Session, limit: int = 25) -> dict:
    limit = min(max(limit, 1), 100)
    runs = list(db.scalars(select(AgentRun).order_by(AgentRun.started_at.desc()).limit(limit)).all())
    rows = [_run_performance_row(db, run) for run in runs]
    latencies = [row["total_latency_ms"] for row in rows if row["total_latency_ms"] is not None]
    model_calls = [row["total_model_calls"] for row in rows]

    return {
        "summary": {
            "average_latency_ms": round(mean(latencies), 2) if latencies else 0,
            "p95_latency_ms": _percentile(latencies, 0.95),
            "average_model_calls": round(mean(model_calls), 2) if model_calls else 0,
            "slow_runs_count": sum(1 for latency in latencies if latency > 30_000),
        },
        "runs": rows,
    }


def _run_performance_row(db: Session, run: AgentRun) -> dict:
    events = list(
        db.scalars(
            select(AgentTraceEvent)
            .where(AgentTraceEvent.agent_run_id == run.id)
            .order_by(AgentTraceEvent.latency_ms.desc())
        ).all()
    )
    slowest = next((event for event in events if event.latency_ms is not None), None)
    return {
        "agent_run_id": run.id,
        "conversation_id": run.conversation_id,
        "status": run.status,
        "total_latency_ms": run.total_latency_ms,
        "total_model_calls": run.total_model_calls,
        "model_provider": run.model_provider,
        "model_name": run.model_name,
        "slowest_node_name": slowest.node_name if slowest else None,
        "slowest_node_latency_ms": slowest.latency_ms if slowest else None,
        "created_at": run.started_at.isoformat(),
    }


def _percentile(values: list[int], percentile: float) -> float:
    if not values:
        return 0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, int(round((len(ordered) - 1) * percentile))))
    return float(ordered[index])
