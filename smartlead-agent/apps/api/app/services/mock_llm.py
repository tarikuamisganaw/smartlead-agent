import re

from app.schemas import FinalResponse, IntentResult, LeadInfo
from app.workflow.state import AgentState


PRICING_KEYWORDS = ("price", "pricing", "cost", "how much")
LEAD_KEYWORDS = (
    "seo",
    "website",
    "ads",
    "marketing",
    "automation",
    "lead generation",
    "need help",
    "my budget",
)
DISCOUNT_KEYWORDS = (
    "discount",
    "refund",
    "guarantee",
    "promise results",
    "can you guarantee",
    "70% off",
    "free service",
)
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
    name_match = re.search(
        r"\b(?:my name is|i am|i'm)\s+([A-Za-z]+(?:\s+(?!and\b)[A-Za-z]+)?)(?=\s+and\b|,|\.|$)",
        message,
        flags=re.IGNORECASE,
    )

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
        name=_normalize_name(name_match.group(1)) if name_match else None,
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
    docs = state.get("retrieved_docs") or []

    if intent == "pricing_question":
        message = _pricing_response_from_docs(docs)
        return FinalResponse(message=message, next_step="Share the service and budget so we can qualify the lead.")

    if intent == "lead_inquiry":
        service = lead_info.get("service_interest") or "the right service"
        message = f"Yes, we can help with {service}. "
        pricing_hint = _pricing_hint_for_service(service, docs)
        if pricing_hint:
            message += f"{pricing_hint} "
        if missing_fields:
            missing = " and ".join(missing_fields)
            message += f"To route this properly, please share your {missing}."
            return FinalResponse(message=message, next_step=f"Collect missing lead fields: {missing}.")
        message += "Thanks for the details. The team would review your request and follow up with next steps."
        return FinalResponse(message=message, next_step="Owner notification would be sent.")

    if intent == "discount_request":
        return FinalResponse(
            message="That request needs review by the team. I can collect your details and have someone follow up.",
            next_step="Create a human approval request.",
        )

    if intent == "support_request":
        return FinalResponse(
            message="The team can help with that. Please share what happened, when it started, and any screenshots or error details.",
            next_step="Collect support details.",
        )

    if intent == "faq_question":
        if docs:
            titles = _doc_titles(docs)
            return FinalResponse(
                message=f"Based on the business documents ({titles}), the team can help confirm the best next step after a short discovery call.",
                next_step="Use retrieved documentation to answer the question.",
            )
        return FinalResponse(
            message="I could not find that in the business documents, but I can collect your details and have the team confirm.",
            next_step="Collect details for team follow-up.",
        )

    return FinalResponse(
        message="I want to make sure I understand. Are you asking about pricing, services, support, or starting a new project?",
        next_step="Clarify user intent.",
    )


def _extract_budget(message: str) -> int | None:
    patterns = (
        r"(?:budget(?:\s+is|\s+of|:)?|spend(?:ing)?|around)\s*\$?\s*(\d[\d,]*)",
        r"\$[\s]*(\d[\d,]*)",
        r"\b(\d[\d,]*)\s*(?:budget|dollar|usd)\b",
    )
    match = None
    for pattern in patterns:
        match = re.search(pattern, message, flags=re.IGNORECASE)
        if match:
            break
    if not match:
        return None
    return int(match.group(1).replace(",", ""))


def _normalize_name(name: str) -> str:
    return " ".join(part.capitalize() for part in name.split())


def _extract_service_interest(lowered: str) -> str | None:
    service_patterns = (
        ("paid ads", ("paid ads", "google ads", "facebook ads", "ads")),
        ("website design", ("website design", "web design", "website")),
        ("AI automation", ("ai automation", "automation")),
        ("lead generation", ("lead generation", "lead gen")),
        ("SEO", ("seo",)),
        ("marketing", ("marketing",)),
    )
    for label, keywords in service_patterns:
        if any(keyword in lowered for keyword in keywords):
            return label
    return None


def _extract_business_type(lowered: str) -> str | None:
    for business_type in ("gym", "ecommerce", "real estate", "agency", "restaurant", "clinic", "coach", "startup"):
        if business_type in lowered:
            return business_type
    return None


def _extract_timeline(lowered: str) -> str | None:
    for timeline in ("this week", "next week", "next month", "today", "asap", "in 2 weeks", "in 30 days"):
        if timeline in lowered:
            return "ASAP" if timeline == "asap" else timeline
    return None


def _pricing_response_from_docs(docs: list[dict]) -> str:
    pricing_docs = [doc for doc in docs if "pricing" in doc.get("title", "").lower()]
    docs_to_use = pricing_docs or docs
    text = "\n".join(doc.get("content", "") for doc in docs_to_use)
    if not text:
        return "I could not find that in the business documents, but I can collect your details and have the team confirm."

    prices = re.findall(r"(?:(?:SEO Starter Package|SEO Growth Package|Website Design|Paid Ads Setup|AI Automation Setup)[^.\n$]*\$[\d,]+(?:/month)?)", text)
    if prices:
        joined = "; ".join(dict.fromkeys(price.strip("- ").strip() for price in prices[:4]))
        return f"According to the pricing document, {joined}."

    return "I found the pricing document, but I could not identify a specific price for that question. I can collect your details and have the team confirm."


def _pricing_hint_for_service(service: str, docs: list[dict]) -> str | None:
    if not docs:
        return None
    text = "\n".join(doc.get("content", "") for doc in docs if "pricing" in doc.get("title", "").lower())
    if not text:
        return None

    lowered_service = service.lower()
    patterns = {
        "seo": r"SEO (?:Starter|Growth) Package[^.\n]*\$[\d,]+(?:/month)?",
        "website": r"Website Design[^.\n]*\$[\d,]+",
        "paid ads": r"Paid Ads Setup[^.\n]*\$[\d,]+",
        "automation": r"AI Automation Setup[^.\n]*\$[\d,]+",
    }
    for key, pattern in patterns.items():
        if key in lowered_service:
            matches = re.findall(pattern, text)
            if matches:
                return f"The pricing document lists {' and '.join(matches[:2])}."
    return None


def _doc_titles(docs: list[dict]) -> str:
    titles = [doc.get("title") for doc in docs if doc.get("title")]
    return ", ".join(dict.fromkeys(titles))
