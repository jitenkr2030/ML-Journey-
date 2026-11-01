from fastapi import APIRouter, Request, Response
from pydantic import BaseModel
from typing import Optional
from ..services import auth_service

router = APIRouter(prefix="/api/auth", tags=["Auth"])

class RegisterReq(BaseModel):
    email: str
    password: str
    name: str
    firm_name: Optional[str] = ""
    gstin: Optional[str] = ""
    phone: Optional[str] = ""

class LoginReq(BaseModel):
    email: str
    password: str

class ProfileReq(BaseModel):
    name: Optional[str] = ""
    firm_name: Optional[str] = ""
    gstin: Optional[str] = ""
    phone: Optional[str] = ""

class PasswordReq(BaseModel):
    old_password: str
    new_password: str

@router.post("/register")
async def register(req: RegisterReq, response: Response):
    result = await auth_service.register_user(req.email, req.password, req.name, req.firm_name, req.gstin, req.phone)
    if result["success"]:
        response.set_cookie(key="session_token", value=result["token"], httponly=True, max_age=2592000, samesite="lax")
    return result

@router.post("/login")
async def login(req: LoginReq, response: Response):
    result = await auth_service.login_user(req.email, req.password)
    if result["success"]:
        response.set_cookie(key="session_token", value=result["token"], httponly=True, max_age=2592000, samesite="lax")
    return result

@router.get("/me")
async def me(request: Request):
    token = request.cookies.get("session_token", "")
    if not token:
        return {"success": False, "detail": "Not logged in"}
    user = await auth_service.get_user_by_token(token)
    if not user:
        return {"success": False, "detail": "Session expired"}
    return {"success": True, "user": user}

@router.post("/logout")
async def logout(request: Request, response: Response):
    token = request.cookies.get("session_token", "")
    if token:
        await auth_service.logout_user(token)
    response.delete_cookie("session_token")
    return {"success": True}

@router.put("/profile")
async def update_profile(req: ProfileReq, request: Request):
    token = request.cookies.get("session_token", "")
    user = await auth_service.get_user_by_token(token) if token else None
    if not user:
        return {"success": False, "detail": "Not logged in"}
    return await auth_service.update_profile(user["id"], req.name, req.firm_name, req.gstin, req.phone)

@router.post("/change-password")
async def change_password(req: PasswordReq, request: Request):
    token = request.cookies.get("session_token", "")
    user = await auth_service.get_user_by_token(token) if token else None
    if not user:
        return {"success": False, "detail": "Not logged in"}
    return await auth_service.change_password(user["id"], req.old_password, req.new_password)

@router.get("/activity")
async def get_activity(request: Request):
    token = request.cookies.get("session_token", "")
    user = await auth_service.get_user_by_token(token) if token else None
    if not user:
        return {"success": False, "detail": "Not logged in"}
    activities = await auth_service.get_activity(user["id"])
    return {"success": True, "activities": activities}
