"""
FastAPI application entry point.

Startup sequence:
  1. Setup logging
  2. Load persisted memory from disk
  3. Register all routers
  4. Configure CORS for React frontend
"""

import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from utils.logger import setup_logging
from services import memory
from routers import chat, writing, memory_router

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup."""
    log_level = os.getenv("LOG_LEVEL", "INFO")
    setup_logging(log_level)

    import logging
    logger = logging.getLogger(__name__)
    logger.info("🚀 AI English Tutor backend starting up...")

    # Load persisted error memory
    memory.initialize_memory()
    logger.info("✅ Memory service initialized.")

    yield  # app is running

    logger.info("👋 Shutting down AI English Tutor backend.")


app = FastAPI(
    title="AI English Tutor API",
    description=(
        "Personalized IELTS English tutor with chat correction, "
        "writing feedback, and RAG-based memory system."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ─────────────────────────────────────────────────────────────────────
# Allow the React dev server and production Vercel domain
ORIGINS = [
    "http://localhost:5173",     # Vite dev server
    "http://localhost:3000",     # CRA / alternative
    "https://*.vercel.app",      # Vercel production
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(chat.router)
app.include_router(writing.router)
app.include_router(memory_router.router)


@app.get("/", tags=["Health"])
async def root():
    return {
        "status": "ok",
        "service": "AI English Tutor API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "healthy"}
