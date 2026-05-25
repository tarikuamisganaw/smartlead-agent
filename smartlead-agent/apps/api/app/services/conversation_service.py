from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Conversation, Message, utc_now


def get_or_create_conversation(db: Session, conversation_id: str | None = None) -> Conversation:
    if conversation_id:
        conversation = db.get(Conversation, conversation_id)
        if conversation:
            return conversation
        conversation = Conversation(id=conversation_id)
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        return conversation

    conversation = Conversation()
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


def add_message(db: Session, *, conversation_id: str, role: str, content: str) -> Message:
    message = Message(conversation_id=conversation_id, role=role, content=content)
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
