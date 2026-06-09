import argparse
import shutil
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from app import models  # noqa: F401
from app.config import get_settings
from app.database import Base, engine, SessionLocal
from app.services.auth_service import add_membership, create_user, get_or_create_default_organization
from app.services.document_service import default_demo_data_dir, ingest_documents
from app.services.rag_service import invalidate_rag_index


def main() -> None:
    parser = argparse.ArgumentParser(description="Reset the local development database.")
    parser.add_argument("--yes", action="store_true", help="Confirm destructive local reset.")
    args = parser.parse_args()

    settings = get_settings()
    if not args.yes:
        raise SystemExit("Refusing to reset database without --yes.")
    if settings.environment.lower() == "production":
        raise SystemExit("Refusing to reset database when ENVIRONMENT=production.")

    backup_path = _backup_sqlite_database(settings.database_url)

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        organization = get_or_create_default_organization(db)
        owner_created = False
        if settings.demo_owner_email and settings.demo_owner_password:
            owner = create_user(
                db,
                email=settings.demo_owner_email,
                password=settings.demo_owner_password,
                full_name="Demo Owner",
            )
            add_membership(db, user_id=owner.id, organization_id=organization.id, role="owner")
            owner_created = True
        ingest_result = ingest_documents(db, default_demo_data_dir(), clear_existing=True)
        invalidate_rag_index()
    finally:
        db.close()

    print("Local development database reset complete.")
    print(f"Database backed up: {backup_path or 'no existing SQLite file found'}")
    print("Tables recreated: yes")
    print(f"Default organization created: {settings.default_organization_name}")
    print(f"Demo owner created: {'yes' if owner_created else 'skipped'}")
    print(f"Documents ingested: {ingest_result['documents_ingested']}")
    print(f"Chunks created: {ingest_result['chunks_created']}")


def _backup_sqlite_database(database_url: str) -> str | None:
    if not database_url.startswith("sqlite"):
        return None
    parsed = urlparse(database_url)
    db_path = Path(parsed.path if parsed.path else database_url.replace("sqlite:///", ""))
    if not db_path.is_absolute():
        db_path = Path.cwd() / db_path
    if not db_path.exists():
        return None
    timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    backup_path = db_path.with_name(f"{db_path.name}.backup.{timestamp}")
    shutil.copy2(db_path, backup_path)
    return str(backup_path)


if __name__ == "__main__":
    main()
