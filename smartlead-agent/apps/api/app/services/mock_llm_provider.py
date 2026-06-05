from app.schemas import FinalResponse, IntentResult, LeadInfo
from app.services.llm_provider import LLMProvider
from app.services.mock_llm import mock_classify_intent, mock_extract_lead_info, mock_generate_final_response


class MockLLMProvider(LLMProvider):
    provider_name = "mock"
    model_name = "mock-rules-v1"

    def classify_intent(self, message: str, conversation_context: str | None = None) -> IntentResult:
        return mock_classify_intent(message)

    def extract_lead_info(self, message: str, conversation_context: str | None = None) -> LeadInfo:
        return mock_extract_lead_info(message)

    def generate_final_response(self, state: dict) -> FinalResponse:
        return mock_generate_final_response(state)
