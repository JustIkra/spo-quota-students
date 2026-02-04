"""
FastAPI application entry point.
"""
import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.core.config import settings
from app.core.database import engine, Base, SessionLocal
from app.core.security import get_password_hash
from app.models import User, UserRole, Settings
from app.services import init_settings
from app.api import auth_router, admin_router, operator_router, stats_router


# Configure structured logging (SUGGEST-004)
logging.basicConfig(
    level=logging.INFO,
    format='{"time":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","message":"%(message)s"}',
    datefmt='%Y-%m-%dT%H:%M:%S'
)
logger = logging.getLogger(__name__)


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")


def create_initial_admin():
    """Create initial admin user if not exists."""
    db = SessionLocal()
    try:
        # Check if admin exists
        admin = db.query(User).filter(User.role == UserRole.ADMIN).first()
        if not admin:
            admin = User(
                login=settings.ADMIN_LOGIN,
                password_hash=get_password_hash(settings.ADMIN_PASSWORD),
                role=UserRole.ADMIN,
                spo_id=None
            )
            db.add(admin)
            db.commit()
            logger.info(f"Admin user created with login: {settings.ADMIN_LOGIN}")
        else:
            logger.info("Admin user already exists")

        # Initialize settings
        init_settings(db)
        logger.info("Settings initialized")

    except Exception as e:
        logger.error(f"Error during initialization: {e}")
        db.rollback()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown events."""
    # Startup
    logger.info("Starting application...")
    init_db()
    create_initial_admin()
    yield
    # Shutdown
    logger.info("Shutting down application...")


# Create FastAPI app
app = FastAPI(
    title="SPO Quota Students API",
    description="API for managing student quotas in secondary professional organizations",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
if settings.CORS_ORIGINS == "*":
    logger.warning(
        "CORS_ORIGINS is set to '*' - credentials will be disabled. "
        "Set specific origins for allow_credentials=True support."
    )
    cors_origins = ["*"]
    allow_credentials = False
else:
    cors_origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",")]
    allow_credentials = True

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request ID middleware for tracing (SUGGEST-002)
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add X-Request-ID header to all requests for tracing."""
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    # Store in request state for use in logging
    request.state.request_id = request_id

    response: Response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


# Include routers
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(operator_router)
app.include_router(stats_router)


@app.get("/", tags=["Health"])
def root():
    """Health check endpoint."""
    return {"status": "ok", "message": "SPO Quota Students API is running"}


@app.get("/health", tags=["Health"])
def health_check():
    """
    Health check endpoint with database connectivity check (SUGGEST-003).
    Returns status of the application and its dependencies.
    """
    health_status = {
        "status": "healthy",
        "checks": {
            "database": "unknown"
        }
    }

    # Check database connectivity
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        health_status["checks"]["database"] = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health_status["status"] = "unhealthy"
        health_status["checks"]["database"] = "unhealthy"

    return health_status
