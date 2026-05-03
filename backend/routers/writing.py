"""
Writing Router — /writing endpoint for IELTS essay evaluation.
"""

import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException

from models.schemas import (
    WritingRequest, WritingResponse,
    WritingCorrection, IELTSScore,
)
from services import ai_service, memory, rag

router = APIRouter(prefix="/writing", tags=["Writing"])
logger = logging.getLogger(__name__)


@router.post("", response_model=WritingResponse)
async def writing_endpoint(request: WritingRequest):
    user_id = request.user_id
    text = request.text.strip()
    task_type = request.task_type

    if len(text) < 10:
        raise HTTPException(status_code=400, detail="Text too short for evaluation.")

    # ── Retrieve RAG context ─────────────────────────────────────────────────
    if user_id not in rag._indices:
        error_texts = memory.get_error_texts(user_id)
        rag.initialize_user_index(user_id, error_texts)

    context = rag.retrieve_context(user_id, text[:200], top_k=3)

    # ── Call AI ──────────────────────────────────────────────────────────────
    try:
        ai_result = await ai_service.call_writing_ai(text, task_type, context)
    except Exception as exc:
        logger.error("OpenAI writing call failed: %s", exc)
        raise HTTPException(status_code=502, detail=f"AI service error: {str(exc)}")

    # ── Parse response ───────────────────────────────────────────────────────
    try:
        corrections = [
            WritingCorrection(
                original_sentence=c.get("original_sentence", ""),
                corrected_sentence=c.get("corrected_sentence", ""),
                issue=c.get("issue", ""),
                suggestion=c.get("suggestion", ""),
            )
            for c in ai_result.get("corrections", [])
        ]

        raw_score = ai_result.get("ielts_score", {})
        ielts_score = IELTSScore(
            task_achievement=_clamp(raw_score.get("task_achievement", 5.0)),
            coherence_cohesion=_clamp(raw_score.get("coherence_cohesion", 5.0)),
            lexical_resource=_clamp(raw_score.get("lexical_resource", 5.0)),
            grammatical_range=_clamp(raw_score.get("grammatical_range", 5.0)),
            estimated_band=_clamp(raw_score.get("estimated_band", 5.0)),
        )
    except Exception as exc:
        logger.error("Writing response parsing error: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to parse AI response.")

    # ── Store grammar errors in memory for RAG ───────────────────────────────
    grammar_errors = [
        {
            "error_type": c.issue,
            "original": c.original_sentence,
            "corrected": c.corrected_sentence,
            "explanation": c.suggestion,
        }
        for c in corrections
    ]
    memory.add_errors(user_id, grammar_errors)
    if grammar_errors:
        texts = [
            f"{e['error_type']}: \"{e['original'][:60]}\" → \"{e['corrected'][:60]}\""
            for e in grammar_errors
        ]
        rag.add_texts_to_index(user_id, texts)

    return WritingResponse(
        overall_feedback=ai_result.get("overall_feedback", ""),
        corrections=corrections,
        ielts_score=ielts_score,
        strengths=ai_result.get("strengths", []),
        areas_to_improve=ai_result.get("areas_to_improve", []),
        timestamp=datetime.utcnow(),
    )


def _clamp(value, lo: float = 0.0, hi: float = 9.0) -> float:
    try:
        return max(lo, min(hi, float(value)))
    except (TypeError, ValueError):
        return 5.0
