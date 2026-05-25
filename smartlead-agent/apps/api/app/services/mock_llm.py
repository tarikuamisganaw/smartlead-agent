import re

from app.schemas import FinalResponse, IntentResult, LeadInfo
from app.workflow.state import AgentState


PRICING_KEYWORDS = ("price", "pricing", "cost", "how much")
LEAD_KEYWORDS = ("seo", "website", "ads", "marketing", "automation", "need help", "my budget")
DISCOUNT_KEYWORDS = ("discount", "refund", "guarantee", "promise results")
SUPPORT_KEYWORDS = ("support", "problem", "issue", "broken")


def _contains_any(message: str, keywords: tuple[str, ...]) -> bool:
    lowered = message.lower()
    return any(keyword in lowered for keyword in keywords)


def mock_classify_intent(message: str) -> IntentResult:
    lowered = message.lower()

    if _contains_any(lowered, DISCOUNT_KEYWORDS):
        return IntentResult(
            intent="discount_request",
            confidence=0.94,
            needs_rag=True,
            requires_human_approval=True,
            reason="Message asks about discount, refund, guarantee, or promised results.",
        )

    if _contains_any(lowered, PRICING_KEYWORDS):
        return IntentResult(
            intent="pricing_question",
            confidence=0.91,
            needs_rag=True,
            requires_human_approval=False,
            reason="Message asks about price or cost.",
        )

    if _contains_any(lowered, SUPPORT_KEYWORDS):
        return IntentResult(
            intent="support_request",
            confidence=0.88,
            needs_rag=False,
            requires_human_approval=False,
            reason="Message describes a support issue.",
        )

    if _contains_any(lowered, LEAD_KEYWORDS):
        return IntentResult(
            intent="lead_inquiry",
            confidence=0.89,
            needs_rag=True,
            requires_human_approval=False,
            reason="Message includes service or buying signals.",
        )

    if any(token in lowered for token in ("what", "when", "where", "who", "can you", "do you", "how")):
        return IntentResult(
            intent="faq_question",
            confidence=0.72,
            needs_rag=True,
            requires_human_approval=False,
            reason="Message appears to be a general question.",
        )

    return IntentResult(
        intent="unknown",
        confidence=0.45,
        needs_rag=False,
        requires_human_approval=False,
        reason="No strong intent pattern matched.",
    )


def mock_extract_lead_info(message: str) -> LeadInfo:
    lowered = message.lower()
    email_match = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", message)
    phone_match = re.search(r"(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)\d{3}[-.\s]?\d{4}", message)
    name_match = re.search(r"\b(?:my name is|i am|i'm)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)", message)

    budget = _extract_budget(message)
    service_interest = _extract_service_interest(lowered)
    business_type = _extract_business_type(lowered)
    timeline = _extract_timeline(lowered)

    missing_fields = []
    if not name_match:
        missing_fields.append("name")
    if not email_match:
        missing_fields.append("email")

    return LeadInfo(
        name=name_match.group(1) if name_match else None,
        email=email_match.group(0) if email_match else None,
        phone=phone_match.group(0) if phone_match else None,
        business_type=business_type,
        service_interest=service_interest,
        budget=budget,
        timeline=timeline,
        missing_fields=missing_fields,
    )


def mock_generate_final_response(state: AgentState) -> FinalResponse:
    intent = state.get("intent") or "unknown"
    lead_info = state.get("lead_info") or {}
    missing_fields = state.get("missing_lead_fields") or []

    if intent == "pricing_question":
        message = (
            "Our mock Week 1 pricing answer: SEO starts around $1,500/month, website design starts around "
            "$2,000, paid ads setup starts around $800, and AI automation setup starts around $1,200. "
            "In Week 2 this answer will be grounded in retrieved docs."
        )
        return FinalResponse(message=message, next_step="Share the service and budget so we can qualify the lead.")

    if intent == "lead_inquiry":
        service = lead_info.get("service_interest") or "the right service"
        message = f"Yes, we can help with {service}. "
        if missing_fields:
            missing = " and ".join(missing_fields)
            message += f"To route this properly, please share your {missing}."
            return FinalResponse(message=message, next_step=f"Collect missing lead fields: {missing}.")
        message += "Thanks for the details. The team would review your request and follow up with next steps."
        return FinalResponse(message=message, next_step="Owner notification would be sent.")

    if intent == "discount_request":
        return FinalResponse(
            message="Special pricing, refunds, guarantees, and promised-results requests need team review before approval.",
            next_step="Create a human approval request.",
        )

    if intent == "support_request":
        return FinalResponse(
            message="The team can help with that. Please share what happened, when it started, and any screenshots or error details.",
            next_step="Collect support details.",
        )

    if intent == "faq_question":
        return FinalResponse(
            message="Here is a mock Week 1 answer based on the demo business docs. We usually start with a short discovery step and then recommend the best service path.",
            next_step="Answer with real retrieved documentation in Week 2.",
        )

    return FinalResponse(
        message="I want to make sure I understand. Are you asking about pricing, services, support, or starting a new project?",
        next_step="Clarify user intent.",
    )


def _extract_budget(message: str) -> int | None:
    explicit_budget = re.search(
        r"(?:budget(?:\s+is|\s+of|:)?|spend(?:ing)?|around)\s*\$?\s*(\d[\d,]*)",
        message,
        flags=re.IGNORECASE,
    )
    dollar_amount = re.search(r"\$\s*(\d[\d,]*)", message)
    match = explicit_budget or dollar_amount
    if not match:
        return None
    return int(match.group(1).replace(",", ""))


def _extract_service_interest(lowered: str) -> str | None:
    service_patterns = (
        ("paid ads", ("paid ads", "google ads", "facebook ads", "ads")),
        ("website design", ("website design", "web design", "website")),
        ("AI automation", ("ai automation", "automation")),
        ("SEO", ("seo",)),
        ("marketing", ("marketing",)),
    )
    for label, keywords in service_patterns:
        if any(keyword in lowered for keyword in keywords):
            return label
    return None


def _extract_business_type(lowered: str) -> str | None:
    for business_type in ("gym", "ecommerce", "real estate", "agency", "restaurant"):
        if business_type in lowered:
            return business_type
    return None


def _extract_timeline(lowered: str) -> str | None:
    for timeline in ("this week", "next week", "next month", "today", "asap"):
        if timeline in lowered:
            return "ASAP" if timeline == "asap" else timeline
    return None
