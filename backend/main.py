"""
FastAPI application entry point.

Improvements:
- Better logging visibility
- Safer CORS config
- Health check + debug info
- Ready for production scaling
"""

import os
from contextlib import asynccontextmanager
import logging

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from utils.logger import setup_logging
from services import memory
from routers import chat, writing, memory_router

# Load env first
load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup."""

    log_level = os.getenv("LOG_LEVEL", "INFO")
    setup_logging(log_level)

    logger = logging.getLogger("app")

    logger.info("🚀 Starting AI English Tutor backend...")

    try:
        # 🔥 Load persisted memory
        memory.initialize_memory()
        logger.info("✅ Memory initialized successfully.")

    except Exception as e:
        logger.error("❌ Memory initialization failed: %s", e)

    yield  # app is running

    logger.info("👋 Shutting down AI English Tutor backend.")


app = FastAPI(
    title="AI English Tutor API",
    description=(
        "Personalized IELTS English tutor with chat correction, "
        "writing feedback, and RAG-based memory system."
    ),
    version="1.1.0",
    lifespan=lifespan,
)

# ── CORS ─────────────────────────────────────────

# ⚠️ NOTE: wildcard like *.vercel.app does NOT work directly in FastAPI
ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:3000",
]

# 👉 Optional: allow all in dev
if os.getenv("ENV") == "dev":
    ALLOWED_ORIGINS = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ──────────────────────────────────────

app.include_router(chat.router)
app.include_router(writing.router, prefix="/writing", tags=["Writing"])
app.include_router(memory_router.router, prefix="/memory", tags=["Memory"])

# ── Health & Debug ───────────────────────────────

@app.get("/", tags=["Health"])
async def root():
    return {
        "status": "ok",
        "service": "AI English Tutor API",
        "version": app.version,
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
async def health():
    return {
        "status": "healthy",
        "env": os.getenv("ENV", "unknown"),
    }


@app.get("/debug/memory", tags=["Debug"])
async def debug_memory():
    """
    Debug endpoint to check memory state
    (useful when testing RAG)
    """
    try:
        from services.rag_service import _texts
        return {
            "users": len(_texts),
            "memory_preview": {
                user: texts[:3] for user, texts in _texts.items()
            }
        }
    except Exception as e:
        return {"error": str(e)}