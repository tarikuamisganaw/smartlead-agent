from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Lead


def list_leads(db: Session) -> list[Lead]:
    statement = select(Lead).order_by(Lead.created_at.desc())
    return list(db.scalars(statement).all())
