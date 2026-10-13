from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
import logging

from app.services.usage_service import (
    check_limit, consume_usage, get_usage_status
)
from app.services.auth_service import get_user_by_token

logger = logging.getLogger(__name__)
router = APIRouter()


class ConsumeRequest(BaseModel):
    recon_type: str


async def _get_user(request: Request):
    token = request.cookies.get("session_token", "")
    if not token:
        raise HTTPException(status_code=401, detail="Login required")
    user = await get_user_by_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Session expired")
    return user


@router.get("/api/usage")
async def get_usage(request: Request):
    user = await _get_user(request)
    status = await get_usage_status(user["email"])
    return {"success": True, **status}


@router.post("/api/usage/check")
async def check(request: Request, data: ConsumeRequest):
    user = await _get_user(request)
    result = await check_limit(user["email"], data.recon_type)
    return {"success": True, **result}


@router.post("/api/usage/consume")
async def consume(request: Request, data: ConsumeRequest):
    user = await _get_user(request)
    result = await consume_usage(user["email"], data.recon_type)
    return {"success": True, **result}
