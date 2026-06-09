from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import models  # noqa: F401
from app.api.routes import router
from app.config import get_settings
from app.database import init_db


def create_app() -> FastAPI:
    init_db()
    settings = get_settings()
    app = FastAPI(title="SmartLead Agent API", version="0.1.0")
    local_dev_origin_regex = None
    if settings.environment.lower() == "development":
        local_dev_origin_regex = r"https?://(localhost|127\.0\.0\.1):\d+"

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", settings.frontend_url],
        allow_origin_regex=local_dev_origin_regex,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router)

    @app.get("/")
    async def root() -> dict:
        return {"service": settings.service_name, "docs": "/docs"}

    return app


app = create_app()
