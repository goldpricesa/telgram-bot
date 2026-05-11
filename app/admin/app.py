from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.admin.routes import (
    admins,
    appeals,
    banned_words,
    canned_messages,
    dashboard,
    kb,
    login,
    questions,
    settings as settings_routes,
    users,
    violations,
)
from app.core.config import get_settings

STATIC_DIR = Path(__file__).parent / "static"


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Qanon-SA Admin", docs_url=None, redoc_url=None, openapi_url=None)
    base = settings.admin_base_path

    app.mount(f"{base}/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    app.include_router(login.router, prefix=base)
    app.include_router(dashboard.router, prefix=base)
    app.include_router(users.router, prefix=base)
    app.include_router(violations.router, prefix=base)
    app.include_router(questions.router, prefix=base)
    app.include_router(appeals.router, prefix=base)
    app.include_router(banned_words.router, prefix=base)
    app.include_router(canned_messages.router, prefix=base)
    app.include_router(settings_routes.router, prefix=base)
    app.include_router(admins.router, prefix=base)
    app.include_router(kb.router, prefix=base)

    return app
