from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Lead


def list_leads(db: Session) -> list[Lead]:
    statement = select(Lead).order_by(Lead.created_at.desc())
    return list(db.scalars(statement).all())


def get_latest_lead_for_conversation(db: Session, conversation_id: str) -> Lead | None:
    statement = (
        select(Lead)
        .where(Lead.conversation_id == conversation_id)
        .order_by(Lead.created_at.desc())
        .limit(1)
    )
    return db.scalars(statement).first()


def lead_to_dict(lead: Lead | None) -> dict | None:
    if not lead:
        return None
    return {
        "id": lead.id,
        "conversation_id": lead.conversation_id,
        "name": lead.name,
        "email": lead.email,
        "phone": lead.phone,
        "business_type": lead.business_type,
        "service_interest": lead.service_interest,
        "budget": lead.budget,
        "timeline": lead.timeline,
        "lead_score": lead.lead_score,
        "lead_quality": lead.lead_quality,
        "status": lead.status,
        "created_at": lead.created_at.isoformat(),
    }


def merge_lead_info(existing_lead: Lead | dict | None, new_lead_info: dict) -> dict:
    existing = lead_to_dict(existing_lead) if isinstance(existing_lead, Lead) else dict(existing_lead or {})
    merged = {
        "name": existing.get("name"),
        "email": existing.get("email"),
        "phone": existing.get("phone"),
        "business_type": existing.get("business_type"),
        "service_interest": existing.get("service_interest"),
        "budget": existing.get("budget"),
        "timeline": existing.get("timeline"),
    }

    for key in ("name", "email", "phone", "business_type", "service_interest", "budget", "timeline"):
        value = new_lead_info.get(key)
        if value not in (None, "", []):
            merged[key] = value

    merged["missing_fields"] = _missing_lead_fields(merged)
    return merged


def create_or_update_lead(
    db: Session,
    conversation_id: str,
    lead_info: dict,
    lead_score: int | None,
    lead_quality: str | None,
) -> Lead:
    lead = get_latest_lead_for_conversation(db, conversation_id)
    if not lead:
        lead = Lead(conversation_id=conversation_id)

    for field in ("name", "email", "phone", "business_type", "service_interest", "budget", "timeline"):
        value = lead_info.get(field)
        if value not in (None, "", []):
            setattr(lead, field, value)

    lead.lead_score = lead_score
    lead.lead_quality = lead_quality

    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead


def score_lead_info(lead_info: dict) -> tuple[int, str]:
    score = 0

    if lead_info.get("service_interest"):
        score += 20
    if lead_info.get("business_type"):
        score += 10

    budget = lead_info.get("budget")
    if budget is not None:
        if budget >= 3000:
            score += 30
        elif budget >= 1500:
            score += 25
        elif budget > 0:
            score += 15

    timeline = (lead_info.get("timeline") or "").lower()
    if timeline in {"today", "this week", "next week", "asap"}:
        score += 25
    elif timeline in {"next month", "in 2 weeks", "in 30 days"}:
        score += 20
    elif timeline:
        score += 5

    if lead_info.get("email"):
        score += 20
    if lead_info.get("phone"):
        score += 10
    if lead_info.get("name"):
        score += 10

    score = min(score, 100)
    if score <= 39:
        quality = "cold"
    elif score <= 69:
        quality = "warm"
    else:
        quality = "hot"
    return score, quality


def _missing_lead_fields(lead_info: dict) -> list[str]:
    missing = []
    if not lead_info.get("name"):
        missing.append("name")
    if not lead_info.get("email"):
        missing.append("email")
    return missing
