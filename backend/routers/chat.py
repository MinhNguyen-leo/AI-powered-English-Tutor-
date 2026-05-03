"""
Chat Router — /chat endpoint.

Full pipeline:
  1. Retrieve RAG context from user's past errors (FAISS)
  2. Build prompt with context injected
  3. Call OpenAI
  4. Parse structured JSON response
  5. Store new errors in memory + update FAISS index
  6. Return ChatResponse
"""

import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException

from models.schemas import ChatRequest, ChatResponse, ErrorDetail, ScoreDetail
from services import ai_service, memory, rag

router = APIRouter(prefix="/chat", tags=["Chat"])
logger = logging.getLogger(__name__)


@router.post("", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    user_id = request.user_id
    user_message = request.message.strip()

    if not user_message:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    # ── Step 1: ensure user's FAISS index is ready ──────────────────────────
    if user_id not in rag._indices:
        error_texts = memory.get_error_texts(user_id)
        rag.initialize_user_index(user_id, error_texts)

    # ── Step 2: retrieve past-error context ──────────────────────────────────
    context = rag.retrieve_context(user_id, user_message, top_k=3)
    context_used = context is not None

    # ── Step 3: call AI ──────────────────────────────────────────────────────
    try:
        ai_result = await ai_service.call_chat_ai(user_message, context)
    except Exception as exc:
        logger.error("OpenAI call failed: %s", exc)
        raise HTTPException(status_code=502, detail=f"AI service error: {str(exc)}")

    # ── Step 4: parse & validate response ───────────────────────────────────
    try:
        errors = [
            ErrorDetail(
                original=e.get("original", ""),
                corrected=e.get("corrected", ""),
                error_type=e.get("error_type", "unknown"),
                explanation=e.get("explanation", ""),
            )
            for e in ai_result.get("errors", [])
        ]
        raw_score = ai_result.get("score", {})
        score = ScoreDetail(
            grammar=_clamp(raw_score.get("grammar", 5.0)),
            vocabulary=_clamp(raw_score.get("vocabulary", 5.0)),
            overall=_clamp(raw_score.get("overall", 5.0)),
        )
    except Exception as exc:
        logger.error("Response parsing error: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to parse AI response.")

    # ── Step 5: update memory ────────────────────────────────────────────────
    raw_errors = ai_result.get("errors", [])
    memory.add_errors(user_id, raw_errors)
    if raw_errors:
        new_texts = [
            f"{e.get('error_type','')}: \"{e.get('original','')}\" → \"{e.get('corrected','')}\" ({e.get('explanation','')})"
            for e in raw_errors
        ]
        rag.add_texts_to_index(user_id, new_texts)

    # ── Step 6: return ───────────────────────────────────────────────────────
    return ChatResponse(
        corrected_text=ai_result.get("corrected_text", user_message),
        errors=errors,
        explanation=ai_result.get("explanation", ""),
        score=score,
        context_used=context_used,
        timestamp=datetime.utcnow(),
    )


def _clamp(value, lo: float = 0.0, hi: float = 9.0) -> float:
    try:
        return max(lo, min(hi, float(value)))
    except (TypeError, ValueError):
        return 5.0
