import os

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from . import models
from .config import settings
from .database import engine, get_db
from .middleware import AuthenticationMiddleware, RateLimitMiddleware
from .routers import clients, jobs, projects, tasks

# Database initialization
# In production, use migrations: `whatsnext db upgrade` or `alembic upgrade head`
# For development convenience, auto-create can be enabled with AUTO_CREATE_TABLES=true
if os.environ.get("AUTO_CREATE_TABLES", "").lower() in ("true", "1", "yes"):
    models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="WhatsNext API",
    description="Job queue and task management system API",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,  # type: ignore[arg-type]  # Starlette middleware typing limitation
    allow_origins=settings.get_cors_origins(),
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=[settings.cors_allow_methods] if settings.cors_allow_methods == "*" else settings.cors_allow_methods.split(","),
    allow_headers=[settings.cors_allow_headers] if settings.cors_allow_headers == "*" else settings.cors_allow_headers.split(","),
)

# Add rate limiting middleware (if enabled)
if settings.rate_limit_per_minute > 0:
    app.add_middleware(RateLimitMiddleware, requests_per_minute=settings.rate_limit_per_minute)  # type: ignore[arg-type]

# Add authentication middleware (if API keys are configured)
api_keys = settings.get_api_keys()
if api_keys:
    app.add_middleware(AuthenticationMiddleware, api_keys=api_keys)  # type: ignore[arg-type]

app.include_router(jobs.router)
app.include_router(projects.router)
app.include_router(tasks.router)
app.include_router(clients.router)


@app.get("/checkdb")
def check_db(db: Session = Depends(get_db)):
    return {"message": "DB is working"}


@app.get("/")
def check_connection():
    return {"message": "OK"}
