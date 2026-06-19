from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Conversation, Message, utc_now


def get_or_create_conversation(
    db: Session,
    conversation_id: str | None = None,
    *,
    organization_id: str | None = None,
    user_id: str | None = None,
    anonymous_session_id: str | None = None,
) -> Conversation:
    if conversation_id:
        conversation = db.get(Conversation, conversation_id)
        if conversation:
            _apply_conversation_owner(
                conversation,
                organization_id=organization_id,
                user_id=user_id,
                anonymous_session_id=anonymous_session_id,
            )
            db.add(conversation)
            db.commit()
            db.refresh(conversation)
            return conversation
        conversation = Conversation(
            id=conversation_id,
            organization_id=organization_id,
            user_id=user_id,
            anonymous_session_id=anonymous_session_id,
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        return conversation

    conversation = Conversation(
        organization_id=organization_id,
        user_id=user_id,
        anonymous_session_id=anonymous_session_id,
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


def add_message(
    db: Session,
    *,
    conversation_id: str,
    role: str,
    content: str,
    user_id: str | None = None,
    anonymous_session_id: str | None = None,
) -> Message:
    message = Message(
        conversation_id=conversation_id,
        role=role,
        content=content,
        user_id=user_id,
        anonymous_session_id=anonymous_session_id,
    )
    conversation = db.get(Conversation, conversation_id)
    if conversation:
        conversation.updated_at = utc_now()
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def get_conversation_with_messages(db: Session, conversation_id: str) -> Conversation | None:
    statement = (
        select(Conversation)
        .where(Conversation.id == conversation_id)
        .options(selectinload(Conversation.messages))
    )
    return db.scalars(statement).first()


def _apply_conversation_owner(
    conversation: Conversation,
    *,
    organization_id: str | None,
    user_id: str | None,
    anonymous_session_id: str | None,
) -> None:
    if organization_id and not conversation.organization_id:
        conversation.organization_id = organization_id
    if user_id and not conversation.user_id:
        conversation.user_id = user_id
    if anonymous_session_id and not conversation.anonymous_session_id:
        conversation.anonymous_session_id = anonymous_session_id
