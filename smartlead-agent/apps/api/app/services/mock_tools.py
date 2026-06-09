from sqlalchemy.orm import Session

from app.models import Lead
from app.schemas import LeadInfo
from app.services.lead_service import create_or_update_lead


def mock_search_docs(query: str) -> list[dict]:
    lowered = query.lower()
    docs: list[dict] = []

    if any(keyword in lowered for keyword in ("price", "pricing", "cost", "how much")):
        docs.append(
            {
                "source": "pricing.md",
                "title": "Pricing",
                "snippet": "SEO Starter is $1500/month, SEO Growth is $2500/month, and Website Design starts at $2000.",
            }
        )

    if any(keyword in lowered for keyword in ("seo", "website", "ads", "marketing", "automation")):
        docs.append(
            {
                "source": "services.md",
                "title": "Services",
                "snippet": "Services include SEO, paid ads, website design, and AI automation for small businesses.",
            }
        )

    if any(keyword in lowered for keyword in ("refund", "discount", "guarantee", "promise")):
        docs.append(
            {
                "source": "refund-policy.md",
                "title": "Refund Policy",
                "snippet": "Refunds, discounts, guarantees, and promised-results requests require human review.",
            }
        )

    if not docs:
        docs.append(
            {
                "source": "faq.md",
                "title": "FAQ",
                "snippet": "Most projects begin with a discovery step and can start within one to two weeks.",
            }
        )

    return docs


def create_or_update_lead_record(
    db: Session,
    conversation_id: str,
    lead_info: LeadInfo | dict,
    lead_score: int | None,
    lead_quality: str | None,
    organization_id: str | None = None,
    user_id: str | None = None,
    anonymous_session_id: str | None = None,
) -> Lead:
    lead_data = lead_info.model_dump() if isinstance(lead_info, LeadInfo) else dict(lead_info)
    return create_or_update_lead(
        db,
        conversation_id,
        lead_data,
        lead_score,
        lead_quality,
        organization_id=organization_id,
        user_id=user_id,
        anonymous_session_id=anonymous_session_id,
    )


def mock_create_lead_record(
    db: Session,
    conversation_id: str,
    lead_info: LeadInfo | dict,
    lead_score: int | None,
    lead_quality: str | None,
) -> Lead:
    lead_data = lead_info.model_dump() if isinstance(lead_info, LeadInfo) else dict(lead_info)
    lead_data.pop("missing_fields", None)
    lead = Lead(
        conversation_id=conversation_id,
        name=lead_data.get("name"),
        email=lead_data.get("email"),
        phone=lead_data.get("phone"),
        business_type=lead_data.get("business_type"),
        service_interest=lead_data.get("service_interest"),
        budget=lead_data.get("budget"),
        timeline=lead_data.get("timeline"),
        lead_score=lead_score,
        lead_quality=lead_quality,
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead


def mock_send_owner_notification(lead_info: LeadInfo | dict) -> dict:
    lead_data = lead_info.model_dump() if isinstance(lead_info, LeadInfo) else dict(lead_info)
    return {
        "status": "mock_sent",
        "message": "Owner notification would be sent here.",
        "lead_summary": {
            "name": lead_data.get("name"),
            "email": lead_data.get("email"),
            "service_interest": lead_data.get("service_interest"),
            "budget": lead_data.get("budget"),
            "lead_quality": lead_data.get("lead_quality"),
        },
    }


def create_followup_draft(lead_info: LeadInfo | dict, retrieved_docs: list[dict]) -> dict:
    lead_data = lead_info.model_dump() if isinstance(lead_info, LeadInfo) else dict(lead_info)
    service = lead_data.get("service_interest") or "your project"
    name = lead_data.get("name") or "there"
    doc_titles = ", ".join(dict.fromkeys(doc.get("title", "") for doc in retrieved_docs if doc.get("title")))
    context = f" I reviewed {doc_titles}." if doc_titles else ""
    return {
        "status": "draft_created",
        "message": f"Hi {name}, thanks for sharing details about {service}.{context} The team can confirm fit and next steps on a discovery call.",
    }
