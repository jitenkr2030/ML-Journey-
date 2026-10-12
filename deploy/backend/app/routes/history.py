from fastapi import APIRouter, Request, HTTPException
import logging

from app.services.history_service import (
    get_history_list, delete_history_entry, get_stats
)
from app.services.auth_service import get_user_by_token

logger = logging.getLogger(__name__)
router = APIRouter()


async def _get_user(request: Request):
    token = request.cookies.get("session_token", "")
    if not token:
        raise HTTPException(status_code=401, detail="Login required")
    user = await get_user_by_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Session expired")
    return user


@router.get("/api/history")
async def list_history(request: Request, limit: int = 20):
    user = await _get_user(request)
    entries = await get_history_list(user["email"], limit)
    stats = await get_stats(user["email"])
    return {"success": True, "history": entries, "stats": stats}


@router.delete("/api/history/{history_id}")
async def delete_history(history_id: int, request: Request):
    user = await _get_user(request)
    deleted = await delete_history_entry(history_id, user["email"])
    if not deleted:
        raise HTTPException(status_code=404, detail="Entry not found")
    return {"success": True, "message": "Deleted"}
