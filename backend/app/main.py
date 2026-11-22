"""
FastAPI application entry point.

Configures the FastAPI app, middleware, routes, and lifecycle events.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import health, query, schema, session
from app.config import get_settings
from app.database.connection import dispose_engines
from app.database.seed import create_readonly_user, create_tables, seed_database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle manager."""
    # Startup
    logger.info("Starting AgenticSQL backend...")
    settings = get_settings()
    logger.info("LLM Provider: %s, Model: %s", settings.LLM_PROVIDER, settings.LLM_MODEL)

    # Initialize database
    try:
        create_tables()
        seed_database()
        create_readonly_user()
        logger.info("Database initialization complete")
    except Exception as e:
        logger.error("Database initialization failed: %s", e)
        logger.warning("Application will start but queries may fail")

    yield

    # Shutdown
    logger.info("Shutting down AgenticSQL backend...")
    dispose_engines()


# Create FastAPI app
app = FastAPI(
    title="AgenticSQL — AI Data Analyst",
    description=(
        "Agentic Data Analyst with self-correcting Text-to-SQL. "
        "Ask questions about your business data in natural language."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(query.router)
app.include_router(schema.router)
app.include_router(health.router)
app.include_router(session.router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "AgenticSQL — AI Data Analyst",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health",
    }
