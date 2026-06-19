from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select, text

from app import models  # noqa: F401
from app.api.auth_routes import router as auth_router
from app.api.routes import router
from app.config import get_settings
from app.database import SessionLocal, init_db
from app.models import Document, DocumentChunk
from app.services.auth_service import get_or_create_default_organization


def _cors_origins(settings) -> list[str]:
    configured = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]
    return list(dict.fromkeys(["http://localhost:3000", settings.frontend_url, *configured]))


def create_app() -> FastAPI:
    init_db()
    settings = get_settings()
    app = FastAPI(title="SmartLead Agent API", version="0.1.0")
    local_dev_origin_regex = None
    if settings.environment.lower() == "development":
        local_dev_origin_regex = r"https?://(localhost|127\.0\.0\.1):\d+"

    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_origins(settings),
        allow_origin_regex=local_dev_origin_regex,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*", "Authorization", "X-Anonymous-Session-Token"],
    )
    app.include_router(auth_router)
    app.include_router(router)

    @app.get("/")
    async def root() -> dict:
        return {"service": settings.service_name, "docs": "/docs"}

    @app.get("/ready")
    async def ready() -> dict:
        db = SessionLocal()
        try:
            db.execute(text("SELECT 1"))
            documents_count = int(db.scalar(select(func.count()).select_from(Document)) or 0)
            chunks_count = int(db.scalar(select(func.count()).select_from(DocumentChunk)) or 0)
            organization = get_or_create_default_organization(db)
            return {
                "database_connected": True,
                "documents_count": documents_count,
                "chunks_count": chunks_count,
                "rag_ready": chunks_count > 0,
                "default_organization_exists": bool(organization),
            }
        finally:
            db.close()

    return app


app = create_app()
