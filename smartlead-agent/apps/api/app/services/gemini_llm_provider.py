import json
import re
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from app.schemas import FinalResponse, IntentResult, LeadInfo
from app.services.llm_provider import LLMProvider, LLMProviderError

T = TypeVar("T", bound=BaseModel)


class GeminiLLMProvider(LLMProvider):
    provider_name = "gemini"

    def __init__(
        self,
        *,
        api_key: str,
        model_name: str,
        timeout_seconds: int = 30,
        max_retries: int = 1,
    ) -> None:
        if not api_key:
            raise LLMProviderError("GEMINI_API_KEY is required when MODEL_PROVIDER=gemini.")

        try:
            from google import genai
        except Exception as exc:  # pragma: no cover - depends on optional package.
            raise LLMProviderError("google-genai is not installed. Install requirements.txt first.") from exc

        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries

    def classify_intent(self, message: str, conversation_context: str | None = None) -> IntentResult:
        prompt = f"""
Return ONLY valid JSON for this intent classification task.

Allowed intent values:
- faq_question
- pricing_question
- lead_inquiry
- support_request
- discount_request
- unknown

Required JSON shape:
{{
  "intent": "pricing_question",
  "confidence": 0.0,
  "needs_rag": true,
  "requires_human_approval": false,
  "reason": "short reason"
}}

Rules:
- Pricing, service, refund, policy, onboarding, and case-study questions usually need RAG.
- Lead inquiries usually need RAG if they mention services or pricing.
- Discount/refund/guarantee/promise/free-service requests require human approval.
- Do not classify every business question as a lead.

Conversation context:
{conversation_context or "None"}

User message:
{message}
"""
        return self._generate_validated(prompt, IntentResult)

    def extract_lead_info(self, message: str, conversation_context: str | None = None) -> LeadInfo:
        prompt = f"""
Return ONLY valid JSON for lead extraction.

Required JSON shape:
{{
  "name": null,
  "email": null,
  "phone": null,
  "business_type": null,
  "service_interest": null,
  "budget": null,
  "timeline": null,
  "missing_fields": []
}}

Rules:
- Extract only what the user provided or what is clearly present in conversation context.
- Do not invent name, email, phone, budget, or timeline.
- Use null for unknown values.
- Budget must be an integer or null.
- missing_fields should include important missing lead fields, especially name and email.

Conversation context:
{conversation_context or "None"}

User message:
{message}
"""
        return self._generate_validated(prompt, LeadInfo)

    def generate_final_response(self, state: dict) -> FinalResponse:
        prompt = f"""
Return ONLY valid JSON for the final assistant response.

Required JSON shape:
{{
  "message": "concise business-friendly answer",
  "next_step": null
}}

Rules:
- Answer from retrieved_docs when available.
- Do not hallucinate pricing not found in retrieved_docs.
- If no docs are found, say the business team can confirm.
- If requires_human_approval is true, do not approve discounts, refunds, guarantees, free service, or promised results.
- Ask only for missing lead fields.
- Keep the answer concise and business-friendly.

State JSON:
{json.dumps(_state_for_prompt(state), ensure_ascii=False)}
"""
        return self._generate_validated(prompt, FinalResponse)

    def _generate_validated(self, prompt: str, schema: type[T]) -> T:
        errors: list[str] = []
        attempts = self.max_retries + 1
        for _ in range(attempts):
            try:
                text = self._call_gemini(prompt)
                payload = _parse_json_object(text)
                return schema.model_validate(payload)
            except (json.JSONDecodeError, ValidationError, LLMProviderError, TypeError, ValueError) as exc:
                errors.append(str(exc))

        raise LLMProviderError(f"Gemini returned invalid {schema.__name__} after {attempts} attempt(s): {errors[-1]}")

    def _call_gemini(self, prompt: str) -> str:
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config={"response_mime_type": "application/json"},
            )
        except Exception as exc:  # pragma: no cover - requires real provider call.
            raise LLMProviderError(f"Gemini request failed: {exc}") from exc

        text = getattr(response, "text", None)
        if not text:
            raise LLMProviderError("Gemini response did not include text.")
        return text


def _parse_json_object(text: str) -> dict:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        payload = json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
        if not match:
            raise
        payload = json.loads(match.group(0))

    if not isinstance(payload, dict):
        raise ValueError("Expected a JSON object.")
    return payload


def _state_for_prompt(state: dict) -> dict:
    return {
        "user_message": state.get("user_message"),
        "intent": state.get("intent"),
        "retrieved_docs": [
            {
                "title": doc.get("title"),
                "source": doc.get("source"),
                "content": doc.get("content"),
                "score": doc.get("score"),
            }
            for doc in (state.get("retrieved_docs") or [])[:4]
        ],
        "lead_info": state.get("lead_info") or {},
        "missing_lead_fields": state.get("missing_lead_fields") or [],
        "lead_score": state.get("lead_score"),
        "lead_quality": state.get("lead_quality"),
        "requires_human_approval": state.get("requires_human_approval"),
        "approval_reason": state.get("approval_reason"),
    }
