"""API module - FastAPI routers."""
from app.api.auth import router as auth_router
from app.api.admin import router as admin_router
from app.api.operator import router as operator_router
from app.api.stats import router as stats_router

__all__ = ["auth_router", "admin_router", "operator_router", "stats_router"]
