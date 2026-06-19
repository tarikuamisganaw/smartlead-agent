from collections.abc import AsyncGenerator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    pass


settings = get_settings()
database_url = settings.database_url
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql+psycopg://", 1)
elif database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

engine = create_engine(
                        settings.database_url, 
                        connect_args={"prepare_threshold": None}
                                                    )
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def init_db() -> None:
    if settings.environment.lower() == "production" and settings.database_url.startswith("sqlite"):
        print(
            "WARNING: SQLite is not recommended for deployed user data. "
            "Use Postgres for persistent users, chats, leads, and traces."
        )
    _ensure_pgvector_extension()
    Base.metadata.create_all(bind=engine)
    _ensure_sqlite_compat_columns()
    _ensure_postgres_vector_columns()


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
            "external_sync_status": "VARCHAR",
            "external_sync_provider": "VARCHAR",
            "external_sync_id": "VARCHAR",
            "external_synced_at": "DATETIME",
            "external_sync_error": "TEXT",
            "last_sync_attempt_at": "DATETIME",
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
            "embedding_json": "TEXT",
            "embedding_model": "VARCHAR",
            "embedding_dimension": "INTEGER",
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


def _is_postgres() -> bool:
    return engine.dialect.name == "postgresql"


def _vector_rag_requested() -> bool:
    return settings.rag_provider.lower().strip() in {"supabase", "pgvector", "vector"}


def _ensure_pgvector_extension() -> None:
    if not _is_postgres() or not _vector_rag_requested():
        return

    try:
        with engine.begin() as connection:
            connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    except Exception as exc:  # pragma: no cover - requires Postgres/pgvector.
        print(f"WARNING: Could not enable pgvector extension automatically: {exc}")


def _ensure_postgres_vector_columns() -> None:
    if not _is_postgres():
        return

    compatibility_statements = [
        "ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS embedding_json TEXT",
        "ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS embedding_model VARCHAR",
        "ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS embedding_dimension INTEGER",
    ]

    try:
        with engine.begin() as connection:
            for statement in compatibility_statements:
                connection.execute(text(statement))
    except Exception as exc:  # pragma: no cover - requires Postgres.
        print(f"WARNING: Could not apply Postgres compatibility columns automatically: {exc}")

    if not _vector_rag_requested():
        return

    dimension = int(settings.rag_vector_dimension)
    vector_statements = [
        f"ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS embedding vector({dimension})"
    ]
    index_statements = [
        "CREATE INDEX IF NOT EXISTS ix_document_chunks_embedding "
        "ON document_chunks USING ivfflat (embedding vector_cosine_ops)"
    ]

    try:
        with engine.begin() as connection:
            for statement in vector_statements:
                connection.execute(text(statement))
    except Exception as exc:  # pragma: no cover - requires Postgres/pgvector.
        print(f"WARNING: Could not apply pgvector column automatically: {exc}")

    try:
        with engine.begin() as connection:
            for statement in index_statements:
                connection.execute(text(statement))
    except Exception as exc:  # pragma: no cover - requires Postgres/pgvector.
        print(f"WARNING: Could not create pgvector index automatically: {exc}")


async def get_db() -> AsyncGenerator[Session, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
