from abc import ABC, abstractmethod

from app.schemas import FinalResponse, IntentResult, LeadInfo


class LLMProviderError(RuntimeError):
    """Raised when an LLM provider cannot return valid structured output."""


class LLMProvider(ABC):
    provider_name: str = "unknown"
    model_name: str | None = None

    @abstractmethod
    def classify_intent(self, message: str, conversation_context: str | None = None) -> IntentResult:
        raise NotImplementedError

    @abstractmethod
    def extract_lead_info(self, message: str, conversation_context: str | None = None) -> LeadInfo:
        raise NotImplementedError

    @abstractmethod
    def generate_final_response(self, state: dict) -> FinalResponse:
        raise NotImplementedError
