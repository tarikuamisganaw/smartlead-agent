import os

import pytest

from app.config import get_settings
from app.schemas import IntentResult
from app.services.llm_service import classify_intent


def test_gemini_integration_skipped_without_key() -> None:
    if not os.getenv("GEMINI_API_KEY"):
        pytest.skip("GEMINI_API_KEY is not set.")


@pytest.mark.skipif(not os.getenv("GEMINI_API_KEY"), reason="GEMINI_API_KEY is not set.")
def test_gemini_structured_outputs_if_key_exists(monkeypatch: pytest.MonkeyPatch) -> None:
    pytest.importorskip("google.genai")
    monkeypatch.setenv("MODEL_PROVIDER", "gemini")
    get_settings.cache_clear()

    result = classify_intent("How much does SEO cost?")

    assert isinstance(result, IntentResult)
    assert result.intent in {
        "faq_question",
        "pricing_question",
        "lead_inquiry",
        "support_request",
        "discount_request",
        "unknown",
    }
