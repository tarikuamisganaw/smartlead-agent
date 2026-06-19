from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import (
    AnonymousSessionResponse,
    AuthLoginRequest,
    AuthMeResponse,
    AuthRegisterRequest,
    AuthTokenResponse,
    ClaimAnonymousSessionRequest,
)
from app.services.auth_service import (
    add_membership,
    authenticate_user,
    claim_anonymous_session,
    create_access_token,
    create_anonymous_session,
    create_user,
    get_current_user_required,
    get_or_create_default_organization,
    list_memberships,
    user_to_dict,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthTokenResponse)
async def register(request: AuthRegisterRequest, db: Session = Depends(get_db)) -> dict:
    user = create_user(db, email=request.email, password=request.password, full_name=request.full_name)
    if request.as_owner:
        organization = get_or_create_default_organization(db)
        add_membership(db, user_id=user.id, organization_id=organization.id, role="owner")
    return {
        "access_token": create_access_token({"sub": user.id}),
        "token_type": "bearer",
        "user": user_to_dict(user),
    }


@router.post("/login", response_model=AuthTokenResponse)
async def login(request: AuthLoginRequest, db: Session = Depends(get_db)) -> dict:
    user = authenticate_user(db, email=request.email, password=request.password)
    return {
        "access_token": create_access_token({"sub": user.id}),
        "token_type": "bearer",
        "user": user_to_dict(user),
    }


@router.get("/me", response_model=AuthMeResponse)
async def me(request: Request, db: Session = Depends(get_db)) -> dict:
    user = get_current_user_required(request, db)
    return {"user": user_to_dict(user), "memberships": list_memberships(db, user.id)}


@router.post("/anonymous-session", response_model=AnonymousSessionResponse)
async def anonymous_session(db: Session = Depends(get_db)) -> dict:
    session = create_anonymous_session(db)
    return {"anonymous_session_id": session.id, "session_token": session.session_token}


@router.post("/claim-anonymous-session")
async def claim_session(
    request_body: ClaimAnonymousSessionRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> dict:
    user = get_current_user_required(request, db)
    return claim_anonymous_session(db, user_id=user.id, session_token=request_body.session_token)
