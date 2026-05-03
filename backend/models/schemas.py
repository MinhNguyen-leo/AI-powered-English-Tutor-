from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ─────────────────────────────────────────
#  Chat endpoint schemas
# ─────────────────────────────────────────

class ChatRequest(BaseModel):
    user_id: str = Field(..., description="Unique identifier for the user session")
    message: str = Field(..., min_length=1, description="The user's English text to be corrected")


class ErrorDetail(BaseModel):
    original: str
    corrected: str
    error_type: str          # e.g. "grammar", "vocabulary", "spelling"
    explanation: str


class ScoreDetail(BaseModel):
    grammar: float = Field(ge=0, le=9)
    vocabulary: float = Field(ge=0, le=9)
    overall: float = Field(ge=0, le=9)


class ChatResponse(BaseModel):
    corrected_text: str
    errors: List[ErrorDetail]
    explanation: str
    score: ScoreDetail
    context_used: bool = False      # True if RAG memory was used
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ─────────────────────────────────────────
#  Writing endpoint schemas
# ─────────────────────────────────────────

class WritingRequest(BaseModel):
    user_id: str
    text: str = Field(..., min_length=10, description="Essay or paragraph text to evaluate")
    task_type: str = Field(default="Task 2", description="IELTS Task 1 or Task 2")


class WritingCorrection(BaseModel):
    original_sentence: str
    corrected_sentence: str
    issue: str
    suggestion: str


class IELTSScore(BaseModel):
    task_achievement: float = Field(ge=0, le=9)
    coherence_cohesion: float = Field(ge=0, le=9)
    lexical_resource: float = Field(ge=0, le=9)
    grammatical_range: float = Field(ge=0, le=9)
    estimated_band: float = Field(ge=0, le=9)


class WritingResponse(BaseModel):
    overall_feedback: str
    corrections: List[WritingCorrection]
    ielts_score: IELTSScore
    strengths: List[str]
    areas_to_improve: List[str]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ─────────────────────────────────────────
#  Memory / Error record
# ─────────────────────────────────────────

class ErrorRecord(BaseModel):
    user_id: str
    error_type: str
    original: str
    corrected: str
    explanation: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
