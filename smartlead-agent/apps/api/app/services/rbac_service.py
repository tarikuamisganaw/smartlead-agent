from fastapi import HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Conversation, OrganizationMembership, User
from app.services.auth_service import get_current_user_optional, get_or_create_default_organization
from app.services.auth_service import get_anonymous_session_by_token

OWNER_ROLES = {"owner"}
ADMIN_READ_ROLES = OWNER_ROLES
ADMIN_WRITE_ROLES = OWNER_ROLES


def user_has_org_role(db: Session, user: User | None, organization_id: str, allowed_roles: set[str]) -> bool:
    if not user:
        return False
    membership = db.scalars(
        select(OrganizationMembership)
        .where(OrganizationMembership.user_id == user.id)
        .where(OrganizationMembership.organization_id == organization_id)
    ).first()
    return bool(membership and membership.role in allowed_roles)


def require_admin_read(db: Session, request: Request) -> User | None:
    return _require_roles(db, request, ADMIN_READ_ROLES)


def require_admin_write(db: Session, request: Request) -> User | None:
    return _require_roles(db, request, ADMIN_WRITE_ROLES)


def can_view_own_conversation(user: User | None, conversation: Conversation) -> bool:
    return bool(user and conversation.user_id == user.id)


def require_conversation_access(db: Session, request: Request, conversation: Conversation) -> User | None:
    settings = get_settings()
    if not settings.auth_enabled:
        return None
    user = get_current_user_optional(request, db)
    if can_view_own_conversation(user, conversation):
        return user
    session = get_anonymous_session_by_token(db, request.headers.get("X-Anonymous-Session-Token"))
    if session and conversation.anonymous_session_id == session.id:
        return user
    organization_id = conversation.organization_id or get_or_create_default_organization(db).id
    if user_has_org_role(db, user, organization_id, ADMIN_READ_ROLES):
        return user
    raise HTTPException(status_code=403, detail="You do not have access to this conversation.")


def _require_roles(db: Session, request: Request, allowed_roles: set[str]) -> User | None:
    settings = get_settings()
    if not settings.auth_enabled:
        return None
    user = get_current_user_optional(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required.")
    organization = get_or_create_default_organization(db)
    if not user_has_org_role(db, user, organization.id, allowed_roles):
        raise HTTPException(status_code=403, detail="Insufficient organization role.")
    return user
