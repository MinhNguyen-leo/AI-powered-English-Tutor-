"""
RAG Service — FAISS-based retrieval of past user errors.

Flow:
  1. After each interaction, new errors are embedded and added to the FAISS index.
  2. Before each AI call, the user's current message is embedded and we retrieve
     the top-k most similar past errors to inject as context.

Per-user indices are stored in memory (dict). For production, serialize
index to disk with faiss.write_index / faiss.read_index.
"""

import logging
from typing import Optional
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)

# Lazy-loaded to avoid slow import at startup
_encoder = None
_indices: dict = {}       # {user_id: faiss.IndexFlatL2}
_texts: dict = {}         # {user_id: [str, ...]}  parallel to index rows

EMBEDDING_DIM = 384       # all-MiniLM-L6-v2 output dimension
MODEL_NAME = "all-MiniLM-L6-v2"


def _get_encoder():
    """Lazily load the sentence-transformers model."""
    global _encoder
    if _encoder is None:
        try:
            from sentence_transformers import SentenceTransformer
            logger.info("Loading embedding model: %s", MODEL_NAME)
            _encoder = SentenceTransformer(MODEL_NAME)
            logger.info("Embedding model loaded.")
        except Exception as exc:
            logger.error("Failed to load embedding model: %s", exc)
            raise
    return _encoder


def _get_index(user_id: str):
    """Return (or create) a FAISS index for a user."""
    if user_id not in _indices:
        try:
            import faiss
            index = faiss.IndexFlatL2(EMBEDDING_DIM)
            _indices[user_id] = index
            _texts[user_id] = []
            logger.debug("Created new FAISS index for user '%s'", user_id)
        except ImportError:
            logger.error("faiss-cpu is not installed. Run: pip install faiss-cpu")
            raise
    return _indices[user_id]


def _embed(texts: list[str]) -> np.ndarray:
    """Convert a list of strings to a float32 numpy array of embeddings."""
    encoder = _get_encoder()
    embeddings = encoder.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
    return embeddings.astype(np.float32)


# ─────────────────────────────────────────
#  Public API
# ─────────────────────────────────────────

def add_texts_to_index(user_id: str, texts: list[str]) -> None:
    """Embed a list of error texts and add them to the user's FAISS index."""
    if not texts:
        return
    try:
        index = _get_index(user_id)
        embeddings = _embed(texts)
        index.add(embeddings)
        _texts[user_id].extend(texts)
        logger.debug("Added %d vectors for user '%s' (total: %d)", len(texts), user_id, index.ntotal)
    except Exception as exc:
        logger.error("Failed to add to FAISS index: %s", exc)


def retrieve_context(user_id: str, query: str, top_k: int = 3) -> Optional[str]:
    """
    Retrieve top-k similar past error texts for the given query.
    Returns a formatted string to inject into the AI prompt, or None if no memories.
    """
    if user_id not in _indices:
        return None

    index = _indices[user_id]
    stored_texts = _texts.get(user_id, [])

    if index.ntotal == 0 or not stored_texts:
        return None

    try:
        query_vec = _embed([query])
        k = min(top_k, index.ntotal)
        distances, indices = index.search(query_vec, k)

        results = []
        for i, idx in enumerate(indices[0]):
            if idx >= 0 and idx < len(stored_texts):
                results.append(f"- {stored_texts[idx]}")

        if not results:
            return None

        context = "Past mistakes to avoid:\n" + "\n".join(results)
        logger.debug("Retrieved %d context items for user '%s'", len(results), user_id)
        return context

    except Exception as exc:
        logger.error("FAISS search failed: %s", exc)
        return None


def initialize_user_index(user_id: str, error_texts: list[str]) -> None:
    """
    Called at startup (or first request) to rebuild a user's index
    from their persisted memory records.
    """
    if error_texts:
        add_texts_to_index(user_id, error_texts)
        logger.info("Rebuilt index for user '%s' with %d records", user_id, len(error_texts))
