import base64
import hashlib
import hmac
import json
import secrets
from datetime import timedelta
from time import time
from typing import Any

from fastapi import Header, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import (
    AnonymousSession,
    Conversation,
    Lead,
    Message,
    Organization,
    OrganizationMembership,
    User,
    utc_now,
)


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 260_000)
    return f"pbkdf2_sha256${salt}${base64.urlsafe_b64encode(digest).decode('ascii')}"


def verify_password(password: str, hashed_password: str) -> bool:
    try:
        algorithm, salt, expected = hashed_password.split("$", 2)
    except ValueError:
        return False
    if algorithm != "pbkdf2_sha256":
        return False
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 260_000)
    actual = base64.urlsafe_b64encode(digest).decode("ascii")
    return hmac.compare_digest(actual, expected)


def create_access_token(data: dict[str, Any]) -> str:
    settings = get_settings()
    expires_at = int(time() + timedelta(minutes=settings.access_token_expire_minutes).total_seconds())
    payload = {**data, "exp": expires_at}
    header = {"alg": settings.jwt_algorithm, "typ": "JWT"}
    signing_input = f"{_b64_json(header)}.{_b64_json(payload)}"
    signature = hmac.new(
        settings.jwt_secret_key.encode("utf-8"),
        signing_input.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return f"{signing_input}.{_b64_bytes(signature)}"


def decode_access_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    try:
        header_part, payload_part, signature_part = token.split(".", 2)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="Invalid access token.") from exc

    signing_input = f"{header_part}.{payload_part}"
    expected = _b64_bytes(
        hmac.new(settings.jwt_secret_key.encode("utf-8"), signing_input.encode("utf-8"), hashlib.sha256).digest()
    )
    if not hmac.compare_digest(expected, signature_part):
        raise HTTPException(status_code=401, detail="Invalid access token signature.")

    payload = json.loads(_b64_decode(payload_part))
    if payload.get("exp", 0) < int(time()):
        raise HTTPException(status_code=401, detail="Access token expired.")
    return payload


def get_current_user_optional(request: Request, db: Session) -> User | None:
    authorization = request.headers.get("Authorization")
    if not authorization:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None
    payload = decode_access_token(token)
    user_id = payload.get("sub")
    if not user_id:
        return None
    user = db.get(User, user_id)
    if not user or not user.is_active:
        return None
    return user


def get_current_user_required(request: Request, db: Session) -> User:
    user = get_current_user_optional(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required.")
    return user


def get_or_create_default_organization(db: Session) -> Organization:
    settings = get_settings()
    slug = _slugify(settings.default_organization_name)
    organization = db.scalars(select(Organization).where(Organization.slug == slug)).first()
    if organization:
        return organization
    organization = Organization(name=settings.default_organization_name, slug=slug)
    db.add(organization)
    db.commit()
    db.refresh(organization)
    return organization


def create_user(db: Session, *, email: str, password: str, full_name: str | None = None) -> User:
    normalized_email = email.strip().lower()
    existing = db.scalars(select(User).where(User.email == normalized_email)).first()
    if existing:
        raise HTTPException(status_code=409, detail="User already exists.")
    user = User(email=normalized_email, hashed_password=hash_password(password), full_name=full_name)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, *, email: str, password: str) -> User:
    normalized_email = email.strip().lower()
    user = db.scalars(select(User).where(User.email == normalized_email)).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="User is inactive.")
    return user


def add_membership(db: Session, *, user_id: str, organization_id: str, role: str) -> OrganizationMembership:
    existing = db.scalars(
        select(OrganizationMembership)
        .where(OrganizationMembership.user_id == user_id)
        .where(OrganizationMembership.organization_id == organization_id)
    ).first()
    if existing:
        existing.role = role
        db.add(existing)
        db.commit()
        db.refresh(existing)
        return existing
    membership = OrganizationMembership(user_id=user_id, organization_id=organization_id, role=role)
    db.add(membership)
    db.commit()
    db.refresh(membership)
    return membership


def list_memberships(db: Session, user_id: str) -> list[dict]:
    rows = db.execute(
        select(OrganizationMembership, Organization)
        .join(Organization, Organization.id == OrganizationMembership.organization_id)
        .where(OrganizationMembership.user_id == user_id)
    ).all()
    return [
        {
            "organization_id": membership.organization_id,
            "organization_name": organization.name,
            "role": membership.role,
        }
        for membership, organization in rows
    ]


def create_anonymous_session(db: Session) -> AnonymousSession:
    session = AnonymousSession(session_token=secrets.token_urlsafe(32), last_seen_at=utc_now())
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_anonymous_session_by_token(db: Session, session_token: str | None) -> AnonymousSession | None:
    if not session_token:
        return None
    session = db.scalars(select(AnonymousSession).where(AnonymousSession.session_token == session_token)).first()
    if session:
        session.last_seen_at = utc_now()
        db.add(session)
        db.commit()
        db.refresh(session)
    return session


def get_or_create_anonymous_session(db: Session, session_token: str | None = None) -> AnonymousSession:
    return get_anonymous_session_by_token(db, session_token) or create_anonymous_session(db)


def claim_anonymous_session(db: Session, *, user_id: str, session_token: str) -> dict:
    session = get_anonymous_session_by_token(db, session_token)
    if not session:
        raise HTTPException(status_code=404, detail="Anonymous session not found.")

    conversation_rows = db.scalars(
        select(Conversation).where(Conversation.anonymous_session_id == session.id)
    ).all()
    lead_rows = db.scalars(select(Lead).where(Lead.anonymous_session_id == session.id)).all()
    message_rows = db.scalars(select(Message).where(Message.anonymous_session_id == session.id)).all()

    for row in [*conversation_rows, *lead_rows, *message_rows]:
        row.user_id = user_id
        db.add(row)
    db.commit()
    return {"claimed_conversations": len(conversation_rows), "claimed_leads": len(lead_rows)}


def user_to_dict(user: User) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat(),
    }


def anonymous_session_from_header(
    db: Session,
    x_anonymous_session_token: str | None = Header(default=None, alias="X-Anonymous-Session-Token"),
) -> AnonymousSession | None:
    return get_anonymous_session_by_token(db, x_anonymous_session_token)


def _b64_json(value: dict[str, Any]) -> str:
    return _b64_bytes(json.dumps(value, separators=(",", ":")).encode("utf-8"))


def _b64_bytes(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _b64_decode(value: str) -> str:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(f"{value}{padding}".encode("ascii")).decode("utf-8")


def _slugify(value: str) -> str:
    slug = "".join(character.lower() if character.isalnum() else "-" for character in value)
    return "-".join(part for part in slug.split("-") if part)
