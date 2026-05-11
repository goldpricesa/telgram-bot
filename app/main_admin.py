from __future__ import annotations

from app.admin.app import create_app
from app.core.logging import configure_logging

configure_logging("admin")
app = create_app()
