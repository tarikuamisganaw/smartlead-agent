from app.database import SessionLocal, init_db
from app.services.document_service import default_demo_data_dir, ingest_documents


def main() -> None:
    init_db()
    db = SessionLocal()
    try:
        result = ingest_documents(db, default_demo_data_dir(), clear_existing=True)
        print(result)
    finally:
        db.close()


if __name__ == "__main__":
    main()
