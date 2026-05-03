"""
AI Service — handles all OpenAI calls and prompt engineering.

System prompt returns structured JSON so the app can parse errors,
scores, and corrections without fragile string parsing.
"""

import os
import json
import logging
from typing import Optional
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
client = None
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# ─────────────────────────────────────────
#  System prompts
# ─────────────────────────────────────────

CHAT_SYSTEM_PROMPT = """You are an expert IELTS English tutor helping learners below band 7.0.

Your job is to analyze the user's English text and return a JSON object with EXACTLY this structure:
{
  "corrected_text": "The full corrected version of what the user wrote",
  "errors": [
    {
      "original": "the exact wrong phrase",
      "corrected": "the correct version",
      "error_type": "grammar|vocabulary|spelling|punctuation",
      "explanation": "Clear, friendly explanation of why it is wrong"
    }
  ],
  "explanation": "Overall 1-2 sentence summary of the main issues",
  "score": {
    "grammar": 6.5,
    "vocabulary": 5.0,
    "overall": 5.5
  }
}

Rules:
- Scores are on the IELTS scale 0–9 (use 0.5 increments).
- Be encouraging and kind, but accurate.
- If the text is already correct, return an empty errors list and high scores.
- IMPORTANT: Return ONLY valid JSON. No markdown, no extra text.
"""

WRITING_SYSTEM_PROMPT = """You are an expert IELTS Writing examiner evaluating a candidate's essay.

Return a JSON object with EXACTLY this structure:
{
  "overall_feedback": "2-3 sentences of overall feedback",
  "corrections": [
    {
      "original_sentence": "the original sentence with an issue",
      "corrected_sentence": "the improved version",
      "issue": "What type of issue (grammar, coherence, vocabulary etc.)",
      "suggestion": "Specific advice for improvement"
    }
  ],
  "ielts_score": {
    "task_achievement": 6.0,
    "coherence_cohesion": 5.5,
    "lexical_resource": 6.0,
    "grammatical_range": 5.5,
    "estimated_band": 5.75
  },
  "strengths": ["strength 1", "strength 2"],
  "areas_to_improve": ["area 1", "area 2"]
}

Rules:
- Scores are on the IELTS scale 0–9 (use 0.5 increments).
- estimated_band is the average of the four sub-scores.
- Provide up to 5 corrections for the most impactful issues only.
- IMPORTANT: Return ONLY valid JSON. No markdown, no extra text.
"""

# ─────────────────────────────────────────
#  Prompt builders
# ─────────────────────────────────────────

def build_chat_prompt(user_message: str, context: Optional[str] = None) -> str:
    """Build the user-facing prompt, injecting RAG context when available."""
    if context:
        return (
            f"[Your past mistakes to keep in mind]\n{context}\n\n"
            f"[Current text to analyze]\n{user_message}"
        )
    return f"[Text to analyze]\n{user_message}"


def build_writing_prompt(text: str, task_type: str, context: Optional[str] = None) -> str:
    """Build the writing evaluation prompt."""
    base = f"[IELTS {task_type} Essay]\n{text}"
    if context:
        base = f"[Recurring issues from past sessions]\n{context}\n\n" + base
    return base


# ─────────────────────────────────────────
#  Mock LLMs for local testing
# ─────────────────────────────────────────

def mock_llm(user_input: str) -> dict:
    """Mock LLM response for testing without OpenAI credits."""
    if "very like" in user_input.lower():
        return {
            "corrected_text": user_input.lower().replace("very like", "really like"),
            "errors": [
                {
                    "original": "very like",
                    "corrected": "really like",
                    "error_type": "grammar",
                    "explanation": "Use 'really' with verbs instead of 'very'."
                }
            ],
            "explanation": "I found a common grammar mistake with 'very like'.",
            "score": {"grammar": 5.0, "vocabulary": 6.0, "overall": 5.5}
        }
    else:
        return {
            "corrected_text": user_input,
            "errors": [],
            "explanation": "Your sentence looks good! Try using more advanced vocabulary next time.",
            "score": {"grammar": 7.0, "vocabulary": 6.0, "overall": 6.5}
        }


def mock_writing_llm(text: str) -> dict:
    """Mock LLM response for writing evaluation."""
    return {
        "overall_feedback": "This is a mock evaluation. Your essay shows a clear structure but lacks complex vocabulary.",
        "corrections": [
            {
                "original_sentence": text[:50] + "..." if len(text) > 50 else text,
                "corrected_sentence": "Improved mock sentence.",
                "issue": "vocabulary",
                "suggestion": "Try to use more academic words."
            }
        ],
        "ielts_score": {
            "task_achievement": 6.0,
            "coherence_cohesion": 6.0,
            "lexical_resource": 5.5,
            "grammatical_range": 6.0,
            "estimated_band": 6.0
        },
        "strengths": ["Clear paragraphs", "Good basic grammar"],
        "areas_to_improve": ["Complex sentences", "Academic vocabulary"]
    }


# ─────────────────────────────────────────
#  OpenAI callers
# ─────────────────────────────────────────

async def call_chat_ai(user_message: str, context: Optional[str] = None) -> dict:

    use_mock = (
        os.getenv("USE_MOCK_LLM", "false").lower() == "true"
        or not os.getenv("OPENAI_API_KEY")
        or "your-openai-api-key-here" in str(os.getenv("OPENAI_API_KEY"))
    )

    if use_mock:
        logger.info("Using MOCK LLM for chat")
        return mock_llm(user_message)

    # 👉 chỉ init khi cần
    global client
    if client is None:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    user_prompt = build_writing_prompt(text, task_type, context)

    response = await client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": CHAT_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
        max_tokens=1500,
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content
    logger.debug("Raw AI response: %s", raw)

    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.error("JSON parse failed: %s | raw: %s", exc, raw)
        # Fallback: return a safe default so the API never crashes
        return _fallback_chat_response(user_message)


async def call_writing_ai(text: str, task_type: str, context: Optional[str] = None) -> dict:
    """
    Call OpenAI for IELTS writing evaluation.
    Returns parsed JSON dict.
    """
    use_mock = (
        os.getenv("USE_MOCK_LLM", "false").lower() == "true"
        or not os.getenv("OPENAI_API_KEY")
        or "your-openai-api-key-here" in str(os.getenv("OPENAI_API_KEY"))
    )

    if use_mock:
        logger.info("Using MOCK LLM for writing")
        return mock_writing_llm(text)

    # 👉 chỉ init khi cần
    global client
    if client is None:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


    user_prompt = build_chat_prompt(user_message, context)

    response = await client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": CHAT_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
        max_tokens=1500,
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content
    logger.debug("Raw writing AI response: %s", raw)

    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.error("Writing JSON parse failed: %s | raw: %s", exc, raw)
        return _fallback_writing_response()


# ─────────────────────────────────────────
#  Fallback responses (graceful degradation)
# ─────────────────────────────────────────

def _fallback_chat_response(original: str) -> dict:
    return {
        "corrected_text": original,
        "errors": [],
        "explanation": "Sorry, I couldn't process the response properly. Please try again.",
        "score": {"grammar": 0.0, "vocabulary": 0.0, "overall": 0.0},
    }


def _fallback_writing_response() -> dict:
    return {
        "overall_feedback": "Sorry, I couldn't evaluate the essay. Please try again.",
        "corrections": [],
        "ielts_score": {
            "task_achievement": 0.0,
            "coherence_cohesion": 0.0,
            "lexical_resource": 0.0,
            "grammatical_range": 0.0,
            "estimated_band": 0.0,
        },
        "strengths": [],
        "areas_to_improve": [],
    }
