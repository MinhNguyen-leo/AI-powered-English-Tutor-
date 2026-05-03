"""
Memory stats router — exposes user history for the frontend HistoryPanel.
"""

from fastapi import APIRouter
from services import memory

router = APIRouter(prefix="/memory", tags=["Memory"])


@router.get("/{user_id}/stats")
async def get_stats(user_id: str):
    """Return error count and breakdown for a user."""
    return memory.get_stats(user_id)


@router.get("/{user_id}/errors")
async def get_errors(user_id: str, limit: int = 20):
    """Return the most recent errors for a user."""
    errors = memory.get_user_errors(user_id)
    return {"user_id": user_id, "errors": errors[-limit:]}
