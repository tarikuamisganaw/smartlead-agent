from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from typing import Generic, TypeVar

from app.config import get_settings
from app.schemas import FinalResponse, IntentResult, LeadInfo
from app.services.llm_provider import LLMProvider, LLMProviderError
from app.services.mock_llm_provider import MockLLMProvider

T = TypeVar("T")
_LLM_EXECUTOR = ThreadPoolExecutor(max_workers=4)


@dataclass
class LLMCallResult(Generic[T]):
    value: T
    provider: str
    model: str | None
    fallback_used: bool = False
    error_message: str | None = None


def get_llm_provider() -> LLMProvider:
    settings = get_settings()
    provider = settings.model_provider.lower().strip()

    if provider == "gemini":
        if not settings.gemini_api_key:
            raise LLMProviderError("GEMINI_API_KEY is required when MODEL_PROVIDER=gemini.")
        from app.services.gemini_llm_provider import GeminiLLMProvider

        return GeminiLLMProvider(
            api_key=settings.gemini_api_key,
            model_name=settings.gemini_model,
            timeout_seconds=settings.llm_timeout_seconds,
            max_retries=settings.llm_max_retries,
        )

    return MockLLMProvider()


def classify_intent(message: str, conversation_context: str | None = None) -> IntentResult:
    return classify_intent_with_metadata(message, conversation_context).value


def extract_lead_info(message: str, conversation_context: str | None = None) -> LeadInfo:
    return extract_lead_info_with_metadata(message, conversation_context).value


def generate_final_response(state: dict) -> FinalResponse:
    return generate_final_response_with_metadata(state).value


def classify_intent_with_metadata(message: str, conversation_context: str | None = None) -> LLMCallResult[IntentResult]:
    return _call_with_fallback(lambda provider: provider.classify_intent(message, conversation_context))


def extract_lead_info_with_metadata(message: str, conversation_context: str | None = None) -> LLMCallResult[LeadInfo]:
    return _call_with_fallback(lambda provider: provider.extract_lead_info(message, conversation_context))


def generate_final_response_with_metadata(state: dict) -> LLMCallResult[FinalResponse]:
    try:
        return _call_with_fallback(lambda provider: provider.generate_final_response(state))
    except Exception as exc:  # pragma: no cover - final safety net.
        fallback = FinalResponse(
            message="Sorry, something went wrong while preparing the response. The team can review it.",
            next_step="Team review",
        )
        return LLMCallResult(
            value=fallback,
            provider="safe_fallback",
            model=None,
            fallback_used=True,
            error_message=str(exc),
        )


def _call_with_fallback(call):
    settings = get_settings()
    fallback_provider = MockLLMProvider()
    last_error: Exception | None = None
    for attempt in range(settings.llm_max_retries + 1):
        try:
            provider = get_llm_provider()
            future = _LLM_EXECUTOR.submit(call, provider)
            value = future.result(timeout=settings.llm_node_timeout_seconds)
            return LLMCallResult(value=value, provider=provider.provider_name, model=provider.model_name)
        except TimeoutError as exc:
            last_error = exc
            if attempt >= settings.llm_max_retries:
                break
        except Exception as exc:
            last_error = exc
            if attempt >= settings.llm_max_retries:
                break

    value = call(fallback_provider)
    error_message = "LLM call timed out." if isinstance(last_error, TimeoutError) else str(last_error)
    return LLMCallResult(
        value=value,
        provider=fallback_provider.provider_name,
        model=fallback_provider.model_name,
        fallback_used=True,
        error_message=error_message,
    )
