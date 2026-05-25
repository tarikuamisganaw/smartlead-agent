from fastapi import FastAPI

from app import models  # noqa: F401
from app.api.routes import router
from app.config import get_settings
from app.database import init_db


def create_app() -> FastAPI:
    init_db()
    settings = get_settings()
    app = FastAPI(title="SmartLead Agent API", version="0.1.0")
    app.include_router(router)

    @app.get("/")
    async def root() -> dict:
        return {"service": settings.service_name, "docs": "/docs"}

    return app


app = create_app()
