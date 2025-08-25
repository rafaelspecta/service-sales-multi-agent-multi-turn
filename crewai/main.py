from fastapi import FastAPI

# Load config and observability first
from config.settings import VERBOSE, ALLOW_LIST
from config.observability import langfuse

from agents.registry import AGENTS
from crew.session import get_session
from crew.base_crew import crew

# Import API routers
from routes.webhook import router as webhook_router
from routes.health import router as health_router

# ------------------------------------------------------------------------------
# FastAPI app
# ------------------------------------------------------------------------------
app = FastAPI()

# Register routers
app.include_router(webhook_router)
app.include_router(health_router)
