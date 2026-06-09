from collections.abc import AsyncGenerator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    pass


settings = get_settings()
connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def init_db() -> None:
    if settings.environment.lower() == "production" and settings.database_url.startswith("sqlite"):
        print(
            "WARNING: SQLite is not recommended for deployed user data. "
            "Use Postgres for persistent users, chats, leads, and traces."
        )
    Base.metadata.create_all(bind=engine)
    _ensure_sqlite_compat_columns()


def _ensure_sqlite_compat_columns() -> None:
    if not settings.database_url.startswith("sqlite"):
        return

    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())

    statements = []
    desired_columns = {
        "conversations": {
            "organization_id": "VARCHAR",
            "user_id": "VARCHAR",
            "anonymous_session_id": "VARCHAR",
        },
        "messages": {
            "user_id": "VARCHAR",
            "anonymous_session_id": "VARCHAR",
        },
        "leads": {
            "organization_id": "VARCHAR",
            "user_id": "VARCHAR",
            "anonymous_session_id": "VARCHAR",
        },
        "agent_runs": {
            "organization_id": "VARCHAR",
            "user_id": "VARCHAR",
            "anonymous_session_id": "VARCHAR",
            "model_provider": "VARCHAR",
            "model_name": "VARCHAR",
        },
        "human_approvals": {
            "organization_id": "VARCHAR",
        },
        "documents": {
            "organization_id": "VARCHAR",
        },
        "document_chunks": {
            "organization_id": "VARCHAR",
        },
    }
    for table_name, columns in desired_columns.items():
        if table_name not in table_names:
            continue
        existing_columns = {column["name"] for column in inspector.get_columns(table_name)}
        for column_name, column_type in columns.items():
            if column_name not in existing_columns:
                statements.append(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")

    if not statements:
        return

    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))


async def get_db() -> AsyncGenerator[Session, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
