from app.config import get_settings


def estimate_token_count(text: str | None) -> int:
    if not text:
        return 0
    return max(1, len(text) // 4)


def estimate_llm_cost(
    *,
    model_provider: str | None,
    input_tokens: int = 0,
    output_tokens: int = 0,
) -> float:
    provider = (model_provider or "mock").lower()
    if provider == "mock":
        return 0.0

    settings = get_settings()
    input_cost = (input_tokens / 1_000_000) * settings.estimated_input_cost_per_1m_tokens
    output_cost = (output_tokens / 1_000_000) * settings.estimated_output_cost_per_1m_tokens
    return round(input_cost + output_cost, 8)
