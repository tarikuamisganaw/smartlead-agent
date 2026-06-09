from app.config import get_settings
from app.services.cost_service import estimate_llm_cost, estimate_token_count


def default_model_metadata() -> tuple[str, str | None]:
    settings = get_settings()
    provider = settings.model_provider.lower().strip() or "mock"
    if provider == "gemini":
        return provider, settings.gemini_model
    return "mock", "mock-rules-v1"


def record_model_call(state: dict, *, provider: str, model: str | None) -> None:
    state["model_calls"] = int(state.get("model_calls") or 0) + 1
    state["model_provider"] = provider
    state["model_name"] = model


def collect_agent_run_metrics(state: dict) -> dict:
    provider, model = _provider_and_model_from_state(state)
    input_tokens = _state_input_tokens(state)
    output_tokens = estimate_token_count(state.get("final_response"))

    return {
        "total_model_calls": int(state.get("model_calls") or _count_provider_trace_events(state)),
        "estimated_cost": estimate_llm_cost(
            model_provider=provider,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        ),
        "model_provider": provider,
        "model_name": model,
    }


def _provider_and_model_from_state(state: dict) -> tuple[str, str | None]:
    provider = state.get("model_provider")
    model = state.get("model_name")
    if provider:
        return str(provider), str(model) if model else None
    return default_model_metadata()


def _state_input_tokens(state: dict) -> int:
    pieces = [state.get("user_message") or ""]
    pieces.extend(message.get("content", "") for message in state.get("conversation_history") or [])
    pieces.extend(doc.get("content", "") for doc in state.get("retrieved_docs") or [])
    return sum(estimate_token_count(piece) for piece in pieces)


def _count_provider_trace_events(state: dict) -> int:
    return sum(1 for event in state.get("trace", []) if "provider=" in str(event.get("output_summary") or ""))
