"""
Memory Service — stores user error records between turns.

Persistence strategy: In-memory dict + JSON file on disk.
On startup, existing errors are loaded from the JSON file so
personalization survives server restarts.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────
#  Storage
# ─────────────────────────────────────────

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)
MEMORY_FILE = DATA_DIR / "memory.json"

# In-memory store: {user_id: [ErrorRecord dict, ...]}
_store: dict[str, list] = {}


def _load_from_disk() -> None:
    """Load persisted memory from JSON file at startup."""
    global _store
    if MEMORY_FILE.exists():
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                _store = json.load(f)
            logger.info("Memory loaded: %d users from disk", len(_store))
        except (json.JSONDecodeError, IOError) as e:
            logger.warning("Could not load memory file: %s", e)
            _store = {}


def _save_to_disk() -> None:
    """Persist current memory to JSON file."""
    try:
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(_store, f, ensure_ascii=False, indent=2, default=str)
    except IOError as e:
        logger.error("Could not save memory: %s", e)


# ─────────────────────────────────────────
#  Public API
# ─────────────────────────────────────────

def initialize_memory() -> None:
    """Call once at app startup to load persisted data."""
    _load_from_disk()


def add_errors(user_id: str, errors: List[dict]) -> None:
    """
    Store a list of error dicts extracted from an AI response.
    Each dict should have: error_type, original, corrected, explanation.
    """
    if not errors:
        return

    if user_id not in _store:
        _store[user_id] = []

    for err in errors:
        record = {
            "user_id": user_id,
            "error_type": err.get("error_type", "unknown"),
            "original": err.get("original", ""),
            "corrected": err.get("corrected", ""),
            "explanation": err.get("explanation", ""),
            "timestamp": datetime.utcnow().isoformat(),
        }
        _store[user_id].append(record)

    _save_to_disk()
    logger.debug("Added %d errors for user '%s'", len(errors), user_id)


def get_user_errors(user_id: str) -> List[dict]:
    """Return all stored error records for a user."""
    return _store.get(user_id, [])


def get_error_texts(user_id: str) -> List[str]:
    """
    Return a flat list of text strings suitable for embedding.
    Format: 'error_type: original -> corrected (explanation)'
    """
    records = get_user_errors(user_id)
    texts = []
    for r in records:
        text = (
            f"{r['error_type']}: \"{r['original']}\" → \"{r['corrected']}\" "
            f"({r['explanation']})"
        )
        texts.append(text)
    return texts


def get_stats(user_id: str) -> dict:
    """Return basic stats for the history panel."""
    records = get_user_errors(user_id)
    type_counts: dict = {}
    for r in records:
        t = r.get("error_type", "unknown")
        type_counts[t] = type_counts.get(t, 0) + 1
    return {
        "total_errors": len(records),
        "error_breakdown": type_counts,
    }

memory_store = {
    "u1": [
        {
            "original": "...",
            "corrected": "...",
            "explanation": "...",
            "error_type": "..."
        }
    ]
}

def get_errors(user_id: str):
    """
    Return full error records (list of dict)
    """
    return memory_store.get(user_id, [])
