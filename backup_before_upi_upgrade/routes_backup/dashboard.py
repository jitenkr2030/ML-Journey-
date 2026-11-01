from fastapi import APIRouter, HTTPException, Request

from app.services.auth_service import (
    validate_session, get_dashboard_stats,
    get_user_activity,
)

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


def get_current_user(request: Request) -> dict:
    token = request.cookies.get("session_token")
    user = validate_session(token)
    if not user:
        raise HTTPException(status_code=401, detail="Not logged in")
    return user


@router.get("/stats")
async def dashboard_stats(request: Request):
    user = get_current_user(request)
    stats = get_dashboard_stats(user['user_id'])
    return {"success": True, "stats": stats}


@router.get("/recent")
async def recent_activity(request: Request):
    user = get_current_user(request)
    activities = get_user_activity(user['user_id'], limit=20)
    return {"success": True, "activities": activities}
