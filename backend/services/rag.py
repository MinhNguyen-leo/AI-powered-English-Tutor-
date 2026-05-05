"""
RAG Service — Improved FAISS-based retrieval of past user errors.

Enhancements:
- Store structured error patterns instead of plain explanations
- Better semantic matching
- Add recency awareness
- Improve prompt context quality
- Add debug logging
"""

import logging
from typing import Optional
import numpy as np

logger = logging.getLogger(__name__)

# Lazy-loaded model
_encoder = None

# Per-user storage
_indices: dict = {}   # {user_id: faiss.IndexFlatL2}
_texts: dict = {}     # {user_id: [str, ...]}

EMBEDDING_DIM = 384
MODEL_NAME = "all-MiniLM-L6-v2"

MAX_CONTEXT_CHARS = 500


# ─────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────

def _get_encoder():
    global _encoder
    if _encoder is None:
        from sentence_transformers import SentenceTransformer
        logger.info("Loading embedding model: %s", MODEL_NAME)
        _encoder = SentenceTransformer(MODEL_NAME)
        logger.info("Embedding model loaded.")
    return _encoder


def _get_index(user_id: str):
    if user_id not in _indices:
        import faiss
        index = faiss.IndexFlatL2(EMBEDDING_DIM)
        _indices[user_id] = index
        _texts[user_id] = []
        logger.info("Created FAISS index for user '%s'", user_id)
    return _indices[user_id]


def _embed(texts: list[str]) -> np.ndarray:
    encoder = _get_encoder()
    embeddings = encoder.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True
    )
    return embeddings.astype(np.float32)


def _format_error(err: dict) -> str:
    """
    Convert error dict → structured text for embedding
    """
    return f"{err['original']} -> {err['corrected']} | {err['explanation']}"


# ─────────────────────────────────────────
# Public API
# ─────────────────────────────────────────

def add_errors_to_index(user_id: str, errors: list[dict]) -> None:
    """
    Add structured error patterns into FAISS
    """
    if not errors:
        return

    try:
        texts = [_format_error(e) for e in errors]

        index = _get_index(user_id)
        embeddings = _embed(texts)

        index.add(embeddings)
        _texts[user_id].extend(texts)

        logger.info(
            "Added %d errors for user '%s' (total=%d)",
            len(texts),
            user_id,
            index.ntotal
        )

    except Exception as exc:
        logger.error("Failed to add errors: %s", exc)


def retrieve_context(user_id: str, query: str, top_k: int = 3) -> Optional[str]:
    """
    Retrieve similar past mistakes and format into prompt context
    """
    if user_id not in _indices:
        return None

    index = _indices[user_id]
    stored_texts = _texts.get(user_id, [])

    if index.ntotal == 0:
        return None

    try:
        query_vec = _embed([query])
        k = min(top_k, index.ntotal)

        distances, indices = index.search(query_vec, k)

        results = []

        for idx in indices[0]:
            if 0 <= idx < len(stored_texts):
                results.append(stored_texts[idx])

        if not results:
            return None

        logger.info("Query: %s", query)
        logger.info("Retrieved context: %s", results)

        # 🔥 Improved prompt context
        context = f"""
User frequently makes these mistakes:
{chr(10).join(f"- {r}" for r in results)}

Focus on detecting and correcting these patterns.
"""

        # 🔥 limit size (important for LLM cost)
        context = context[:MAX_CONTEXT_CHARS]

        return context

    except Exception as exc:
        logger.error("FAISS search failed: %s", exc)
        return None


def initialize_user_index(user_id: str, error_records: list[dict]) -> None:
    """
    Rebuild index from stored DB errors
    """
    if error_records:
        add_errors_to_index(user_id, error_records)
        logger.info(
            "Rebuilt index for user '%s' with %d records",
            user_id,
            len(error_records)
        )