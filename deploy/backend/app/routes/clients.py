from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging

from app.services.client_service import (
    add_client, update_client, delete_client,
    list_clients, get_client, search_clients
)
from app.services.auth_service import get_user_by_token

logger = logging.getLogger(__name__)
router = APIRouter()


class ClientData(BaseModel):
    name: str
    gstin: str = ""
    pan: str = ""
    email: str = ""
    phone: str = ""
    address: str = ""
    notes: str = ""


async def _get_user(request: Request):
    token = request.cookies.get("session_token", "")
    if not token:
        raise HTTPException(status_code=401, detail="Login required")
    user = await get_user_by_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Session expired")
    return user


@router.get("/api/clients")
async def get_clients(request: Request, status: str = ""):
    user = await _get_user(request)
    clients = await list_clients(user["email"], status)
    return {"success": True, "clients": clients, "total": len(clients)}


@router.get("/api/clients/search")
async def search(request: Request, q: str = ""):
    user = await _get_user(request)
    if not q:
        return {"success": True, "clients": []}
    clients = await search_clients(user["email"], q)
    return {"success": True, "clients": clients}


@router.get("/api/clients/{client_id}")
async def get_one(request: Request, client_id: int):
    user = await _get_user(request)
    client = await get_client(client_id, user["email"])
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return {"success": True, "client": client}


@router.post("/api/clients")
async def create(request: Request, data: ClientData):
    user = await _get_user(request)
    if not data.name.strip():
        raise HTTPException(status_code=400, detail="Client name is required")
    if data.gstin and len(data.gstin) != 15:
        raise HTTPException(status_code=400, detail="GSTIN must be 15 characters")
    if data.pan and len(data.pan) != 10:
        raise HTTPException(status_code=400, detail="PAN must be 10 characters")
    client = await add_client(user["email"], data.dict())
    return {"success": True, "client": client}


@router.put("/api/clients/{client_id}")
async def update(request: Request, client_id: int, data: ClientData):
    user = await _get_user(request)
    if not data.name.strip():
        raise HTTPException(status_code=400, detail="Client name is required")
    if data.gstin and len(data.gstin) != 15:
        raise HTTPException(status_code=400, detail="GSTIN must be 15 characters")
    if data.pan and len(data.pan) != 10:
        raise HTTPException(status_code=400, detail="PAN must be 10 characters")
    try:
        client = await update_client(client_id, user["email"], data.dict())
        return {"success": True, "client": client}
    except ValueError:
        raise HTTPException(status_code=404, detail="Client not found")


@router.delete("/api/clients/{client_id}")
async def delete(request: Request, client_id: int):
    user = await _get_user(request)
    deleted = await delete_client(client_id, user["email"])
    if not deleted:
        raise HTTPException(status_code=404, detail="Client not found")
    return {"success": True, "message": "Client deleted"}
