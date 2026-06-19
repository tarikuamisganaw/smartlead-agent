from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Lead, utc_now
from app.services.integrations.lead_sync_provider import get_lead_sync_provider


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
        "external_sync_status": lead.external_sync_status,
        "external_sync_provider": lead.external_sync_provider,
        "external_sync_id": lead.external_sync_id,
        "external_synced_at": lead.external_synced_at.isoformat() if lead.external_synced_at else None,
        "external_sync_error": lead.external_sync_error,
        "last_sync_attempt_at": lead.last_sync_attempt_at.isoformat() if lead.last_sync_attempt_at else None,
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
    *,
    organization_id: str | None = None,
    user_id: str | None = None,
    anonymous_session_id: str | None = None,
) -> Lead:
    lead = get_latest_lead_for_conversation(db, conversation_id)
    if not lead:
        lead = Lead(
            conversation_id=conversation_id,
            organization_id=organization_id,
            user_id=user_id,
            anonymous_session_id=anonymous_session_id,
        )
    else:
        if organization_id and not lead.organization_id:
            lead.organization_id = organization_id
        if user_id and not lead.user_id:
            lead.user_id = user_id
        if anonymous_session_id and not lead.anonymous_session_id:
            lead.anonymous_session_id = anonymous_session_id

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


def sync_lead_external(db: Session, lead: Lead, force: bool = False) -> dict:
    provider = get_lead_sync_provider()
    provider_name = provider.provider_name

    lead.external_sync_provider = provider_name
    lead.last_sync_attempt_at = utc_now()
    lead.external_sync_status = "pending"
    lead.external_sync_error = None
    db.add(lead)
    db.commit()
    db.refresh(lead)

    if not provider.is_configured():
        message = f"{provider_name} lead sync provider is not configured."
        lead.external_sync_status = "not_configured"
        lead.external_sync_error = message
        db.add(lead)
        db.commit()
        db.refresh(lead)
        return {
            "status": "not_configured",
            "provider": provider_name,
            "external_id": lead.external_sync_id,
            "message": message,
            "raw": {},
        }

    result = provider.sync_lead(
        lead_to_dict(lead) or {},
        context={"source": "SmartLead Agent", "force": force},
    )
    status = result.get("status") or "failed"
    if status in {"synced", "mock_synced"}:
        lead.external_sync_status = "synced"
        lead.external_sync_provider = provider_name
        lead.external_synced_at = utc_now()
        lead.external_sync_error = None
        if result.get("external_id"):
            lead.external_sync_id = result["external_id"]
    elif status == "skipped":
        lead.external_sync_status = "skipped"
        lead.external_sync_error = result.get("message")
    else:
        lead.external_sync_status = "failed"
        lead.external_sync_error = result.get("message") or "External lead sync failed."

    db.add(lead)
    db.commit()
    db.refresh(lead)
    result["provider"] = result.get("provider") or provider_name
    result["external_id"] = result.get("external_id") or lead.external_sync_id
    return result


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
