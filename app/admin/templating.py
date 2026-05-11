from __future__ import annotations

from pathlib import Path

from fastapi.templating import Jinja2Templates

from app.admin.auth import csrf_token, current_admin
from app.core.config import get_settings
from app.core.constants import CATEGORY_LABEL_AR

TEMPLATES_DIR = Path(__file__).parent / "templates"

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
templates.env.globals["category_labels_ar"] = CATEGORY_LABEL_AR


def _admin_context(request) -> dict:
    return {
        "current_admin": current_admin(request),
        "csrf_token": csrf_token(request) or "",
        "settings": get_settings(),
        "base_path": get_settings().admin_base_path,
    }


def render(request, template: str, **ctx):
    base = _admin_context(request)
    base.update(ctx)
    return templates.TemplateResponse(request, template, base)
