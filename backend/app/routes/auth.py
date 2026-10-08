from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel
from typing import Optional

from app.services.auth_service import (
    register_user, login_user, logout_user,
    validate_session, get_user_profile,
    update_profile, change_password,
    record_activity, get_user_activity,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    firm_name: Optional[str] = ""
    gstin: Optional[str] = ""
    phone: Optional[str] = ""


class LoginRequest(BaseModel):
    email: str
    password: str


class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    firm_name: Optional[str] = None
    gstin: Optional[str] = None
    phone: Optional[str] = None


class PasswordChange(BaseModel):
    old_password: str
    new_password: str


def get_current_user(request: Request) -> dict:
    token = request.cookies.get("session_token")
    user = validate_session(token)
    if not user:
        raise HTTPException(status_code=401, detail="Not logged in")
    return user


@router.post("/register")
async def register(req: RegisterRequest, response: Response):
    if len(req.password) < 6:
        raise HTTPException(
            status_code=400, detail="Password must be 6+ characters"
        )
    if "@" not in req.email:
        raise HTTPException(
            status_code=400, detail="Invalid email"
        )

    result = register_user(
        req.name, req.email, req.password,
        req.firm_name, req.gstin, req.phone
    )

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])

    response.set_cookie(
        key="session_token",
        value=result["token"],
        httponly=True,
        samesite="lax",
        max_age=2592000,  # 30 days
    )

    record_activity(result["user_id"], "register", "account",
                    f"New account: {req.email}")

    return {
        "success": True,
        "name": result["name"],
        "email": result["email"],
        "message": "Account created successfully",
    }


@router.post("/login")
async def login(req: LoginRequest, response: Response):
    result = login_user(req.email, req.password)

    if not result["success"]:
        raise HTTPException(status_code=401, detail=result["error"])

    response.set_cookie(
        key="session_token",
        value=result["token"],
        httponly=True,
        samesite="lax",
        max_age=2592000,
    )

    record_activity(result["user_id"], "login", "account",
                    f"Login: {req.email}")

    return {
        "success": True,
        "name": result["name"],
        "email": result["email"],
        "firm_name": result["firm_name"],
        "message": "Login successful",
    }


@router.post("/logout")
async def logout(request: Request, response: Response):
    token = request.cookies.get("session_token")
    if token:
        logout_user(token)
    response.delete_cookie("session_token")
    return {"success": True, "message": "Logged out"}


@router.get("/me")
async def get_me(request: Request):
    user = get_current_user(request)
    profile = get_user_profile(user['user_id'])
    if not profile:
        raise HTTPException(status_code=404, detail="User not found")
    profile.pop('password_hash', None)
    profile.pop('salt', None)
    return {"success": True, "user": profile}


@router.put("/profile")
async def update_user_profile(
    req: ProfileUpdate, request: Request
):
    user = get_current_user(request)
    success = update_profile(
        user['user_id'], req.name, req.firm_name,
        req.gstin, req.phone
    )
    if not success:
        raise HTTPException(status_code=400, detail="Update failed")

    record_activity(user['user_id'], "update_profile", "account",
                    "Profile updated")

    return {"success": True, "message": "Profile updated"}


@router.post("/change-password")
async def change_user_password(
    req: PasswordChange, request: Request
):
    user = get_current_user(request)
    if len(req.new_password) < 6:
        raise HTTPException(
            status_code=400,
            detail="New password must be 6+ characters"
        )

    result = change_password(
        user['user_id'], req.old_password, req.new_password
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])

    record_activity(user['user_id'], "change_password", "account",
                    "Password changed")

    return {"success": True, "message": "Password changed"}


@router.get("/activity")
async def get_activity(request: Request):
    user = get_current_user(request)
    activities = get_user_activity(user['user_id'])
    return {"success": True, "activities": activities}
