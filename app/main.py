from fastapi import FastAPI

from app.core.config import settings
from app.api.routes import health


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Backend API for an AI-powered chatbot",
    debug=settings.debug
)

app.include_router(health.router)