from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging

from app.services.service_inquiry_service import (
    create_inquiry, list_inquiries, update_inquiry_status, get_inquiry_stats
)
from app.services.auth_service import get_user_by_token

logger = logging.getLogger(__name__)
router = APIRouter()


class InquiryData(BaseModel):
    service_type: str = "manual_accounting"
    name: str
    email: str
    phone: str = ""
    company: str = ""
    gstin: str = ""
    city: str = ""
    message: str = ""
    preferred_time: str = ""


class InquiryUpdate(BaseModel):
    status: str
    notes: str = ""


@router.post("/api/service-inquiry")
async def submit_inquiry(data: InquiryData):
    if not data.name.strip():
        raise HTTPException(status_code=400, detail="Name is required")
    if not data.email.strip() or "@" not in data.email:
        raise HTTPException(status_code=400, detail="Valid email is required")
    inquiry = await create_inquiry(data.dict())
    return {"success": True, "inquiry": inquiry, "message": "Enquiry submitted! We will contact you within 24 hours."}


@router.get("/api/admin/service-inquiries")
async def get_inquiries(request: Request, status: str = "", key: str = ""):
    if not key:
        token = request.cookies.get("session_token", "")
        if token:
            try:
                user = await get_user_by_token(token)
                if user and user.get("is_admin"):
                    key = "session_admin"
            except Exception:
                pass
    if key != "reconcile2026" and key != "session_admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    inquiries = await list_inquiries(status)
    stats = await get_inquiry_stats()
    return {"success": True, "inquiries": inquiries, "stats": stats}


@router.put("/api/admin/service-inquiries/{inquiry_id}")
async def update_inquiry(inquiry_id: int, data: InquiryUpdate, request: Request, key: str = ""):
    if not key:
        token = request.cookies.get("session_token", "")
        if token:
            try:
                user = await get_user_by_token(token)
                if user and user.get("is_admin"):
                    key = "session_admin"
            except Exception:
                pass
    if key != "reconcile2026" and key != "session_admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    updated = await update_inquiry_status(inquiry_id, data.status, data.notes)
    if not updated:
        raise HTTPException(status_code=404, detail="Inquiry not found")
    return {"success": True, "message": "Inquiry updated"}
