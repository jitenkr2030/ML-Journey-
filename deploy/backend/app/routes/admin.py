from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional
import asyncpg
from datetime import datetime, timedelta

from app.services.auth_service import get_user_by_token, get_pool, is_user_admin

router = APIRouter(prefix="/api/admin", tags=["Admin"])


async def _check_admin(request: Request):
    token = request.cookies.get("session_token", "")
    if not token:
        raise HTTPException(status_code=401, detail="Login required")
    user = await get_user_by_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Session expired")
    if not await is_user_admin(user["id"]):
        raise HTTPException(status_code=403, detail="Admin access only")
    return user


# ==================== DASHBOARD STATS ====================
@router.get("/stats")
async def admin_stats(request: Request):
    await _check_admin(request)
    pool = await get_pool()
    async with pool.acquire() as conn:
        total_users = await conn.fetchval("SELECT COUNT(*) FROM users")
        active_sessions = await conn.fetchval("SELECT COUNT(*) FROM sessions WHERE expires_at > NOW()")
        total_activity = await conn.fetchval("SELECT COUNT(*) FROM activity")
        today_users = await conn.fetchval("SELECT COUNT(*) FROM users WHERE created_at::date = CURRENT_DATE")
        today_logins = await conn.fetchval("SELECT COUNT(*) FROM activity WHERE action='login' AND created_at::date = CURRENT_DATE")
        month_users = await conn.fetchval("SELECT COUNT(*) FROM users WHERE created_at >= date_trunc('month', CURRENT_DATE)")
        week_users = await conn.fetchval("SELECT COUNT(*) FROM users WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'")
        total_brs = await conn.fetchval("SELECT COALESCE(SUM(free_brs_used), 0) FROM users")
        total_gst = await conn.fetchval("SELECT COALESCE(SUM(free_gst_used), 0) FROM users")
        total_book = await conn.fetchval("SELECT COALESCE(SUM(free_bookkeeping_used), 0) FROM users")
        total_recon = await conn.fetchval("SELECT COALESCE(SUM(total_reconciliations), 0) FROM users")
        total_revenue = await conn.fetchval("SELECT COALESCE(SUM(total_paid), 0) FROM users")

        # Growth data - last 7 days
        growth = await conn.fetch("""
            SELECT created_at::date as day, COUNT(*) as count
            FROM users
            WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
            GROUP BY day ORDER BY day
        """)

        # Service usage
        service_usage = await conn.fetch("""
            SELECT service_type, COUNT(*) as count
            FROM activity
            WHERE service_type IS NOT NULL AND service_type != 'auth'
            GROUP BY service_type ORDER BY count DESC
        """)

        # Top users
        top_users = await conn.fetch("""
            SELECT name, email, firm_name,
                   (free_brs_used + free_gst_used + free_bookkeeping_used + total_reconciliations) as total_ops,
                   total_paid, created_at, last_login
            FROM users ORDER BY total_ops DESC LIMIT 10
        """)

        return {
            "success": True,
            "stats": {
                "total_users": total_users,
                "active_sessions": active_sessions,
                "total_activity": total_activity,
                "today_new_users": today_users,
                "today_logins": today_logins,
                "week_new_users": week_users,
                "month_new_users": month_users,
                "total_brs": total_brs,
                "total_gst": total_gst,
                "total_bookkeeping": total_book,
                "total_reconciliations": total_recon,
                "total_revenue": float(total_revenue),
                "growth": [{"day": str(g["day"]), "count": g["count"]} for g in growth],
                "service_usage": [{"type": s["service_type"], "count": s["count"]} for s in service_usage],
                "top_users": [dict(u) for u in top_users]
            }
        }


# ==================== USER MANAGEMENT ====================
@router.get("/users")
async def admin_users(request: Request, page: int = 1, per_page: int = 20, search: str = ""):
    await _check_admin(request)
    pool = await get_pool()
    async with pool.acquire() as conn:
        offset = (page - 1) * per_page
        if search:
            pattern = f"%{search}%"
            total = await conn.fetchval(
                "SELECT COUNT(*) FROM users WHERE email ILIKE $1 OR name ILIKE $1 OR firm_name ILIKE $1", pattern
            )
            rows = await conn.fetch("""
                SELECT id, email, name, firm_name, gstin, phone, is_admin,
                       free_brs_used, free_gst_used, free_bookkeeping_used,
                       total_reconciliations, total_paid, created_at, last_login
                FROM users WHERE email ILIKE $1 OR name ILIKE $1 OR firm_name ILIKE $1
                ORDER BY created_at DESC LIMIT $2 OFFSET $3
            """, pattern, per_page, offset)
        else:
            total = await conn.fetchval("SELECT COUNT(*) FROM users")
            rows = await conn.fetch("""
                SELECT id, email, name, firm_name, gstin, phone, is_admin,
                       free_brs_used, free_gst_used, free_bookkeeping_used,
                       total_reconciliations, total_paid, created_at, last_login
                FROM users ORDER BY created_at DESC LIMIT $1 OFFSET $2
            """, per_page, offset)

        return {"success": True, "users": [dict(r) for r in rows], "total": total, "page": page, "pages": (total + per_page - 1) // per_page}


@router.get("/users/{user_id}")
async def get_user_detail(user_id: int, request: Request):
    await _check_admin(request)
    pool = await get_pool()
    async with pool.acquire() as conn:
        user = await conn.fetchrow("""
            SELECT id, email, name, firm_name, gstin, phone, is_admin,
                   free_brs_used, free_gst_used, free_bookkeeping_used,
                   total_reconciliations, total_paid, created_at, last_login
            FROM users WHERE id = $1
        """, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        activity = await conn.fetch("""
            SELECT action, service_type, details, created_at
            FROM activity WHERE user_id = $1 ORDER BY created_at DESC LIMIT 20
        """, user_id)
        sessions = await conn.fetch("""
            SELECT token, created_at, expires_at FROM sessions
            WHERE user_id = $1 AND expires_at > NOW()
        """, user_id)
        return {
            "success": True,
            "user": dict(user),
            "activity": [dict(a) for a in activity],
            "sessions": [{"created_at": str(s["created_at"]), "expires_at": str(s["expires_at"])} for s in sessions]
        }


class UpdateUserReq(BaseModel):
    name: Optional[str] = ""
    firm_name: Optional[str] = ""
    gstin: Optional[str] = ""
    phone: Optional[str] = ""
    is_admin: Optional[bool] = None


@router.put("/users/{user_id}")
async def update_user(user_id: int, req: UpdateUserReq, request: Request):
    await _check_admin(request)
    pool = await get_pool()
    async with pool.acquire() as conn:
        if req.is_admin is not None:
            await conn.execute(
                "UPDATE users SET name=$1, firm_name=$2, gstin=$3, phone=$4, is_admin=$5 WHERE id=$6",
                req.name, req.firm_name, req.gstin, req.phone, req.is_admin, user_id
            )
        else:
            await conn.execute(
                "UPDATE users SET name=$1, firm_name=$2, gstin=$3, phone=$4 WHERE id=$5",
                req.name, req.firm_name, req.gstin, req.phone, user_id
            )
        return {"success": True, "message": "User updated"}


@router.delete("/users/{user_id}")
async def delete_user(user_id: int, request: Request):
    await _check_admin(request)
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM sessions WHERE user_id=$1", user_id)
        await conn.execute("DELETE FROM activity WHERE user_id=$1", user_id)
        await conn.execute("DELETE FROM users WHERE id=$1", user_id)
        return {"success": True, "message": "User deleted"}


@router.post("/users/{user_id}/reset-usage")
async def reset_user_usage(user_id: int, request: Request):
    await _check_admin(request)
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE users SET free_brs_used=0, free_gst_used=0, free_bookkeeping_used=0,
                   total_reconciliations=0, total_paid=0 WHERE id=$1
        """, user_id)
        return {"success": True, "message": "Usage reset"}


@router.post("/users/{user_id}/add-credit")
async def add_credit(user_id: int, request: Request):
    await _check_admin(request)
    body = await request.json()
    service = body.get("service", "")
    pool = await get_pool()
    async with pool.acquire() as conn:
        if service == "brs":
            await conn.execute("UPDATE users SET free_brs_used = GREATEST(0, free_brs_used - $1) WHERE id=$2", body.get("amount", 1), user_id)
        elif service == "gst":
            await conn.execute("UPDATE users SET free_gst_used = GREATEST(0, free_gst_used - $1) WHERE id=$2", body.get("amount", 1), user_id)
        elif service == "bookkeeping":
            await conn.execute("UPDATE users SET free_bookkeeping_used = GREATEST(0, free_bookkeeping_used - $1) WHERE id=$2", body.get("amount", 1), user_id)
        return {"success": True, "message": f"Credit added for {service}"}


@router.post("/users/{user_id}/reset-password")
async def admin_reset_password(user_id: int, request: Request):
    await _check_admin(request)
    body = await request.json()
    new_pass = body.get("password", "Password@123")
    from app.services.auth_service import hash_password
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("UPDATE users SET password_hash=$1 WHERE id=$2", hash_password(new_pass), user_id)
        await conn.execute("DELETE FROM sessions WHERE user_id=$1", user_id)
        return {"success": True, "message": "Password reset and sessions cleared"}


# ==================== ACTIVITY LOG ====================
@router.get("/activity")
async def admin_activity(request: Request, page: int = 1, per_page: int = 50, filter: str = ""):
    await _check_admin(request)
    pool = await get_pool()
    async with pool.acquire() as conn:
        offset = (page - 1) * per_page
        if filter:
            total = await conn.fetchval("SELECT COUNT(*) FROM activity WHERE action = $1", filter)
            rows = await conn.fetch("""
                SELECT a.id, a.action, a.service_type, a.details, a.created_at, u.email, u.name
                FROM activity a JOIN users u ON a.user_id = u.id
                WHERE a.action = $1 ORDER BY a.created_at DESC LIMIT $2 OFFSET $3
            """, filter, per_page, offset)
        else:
            total = await conn.fetchval("SELECT COUNT(*) FROM activity")
            rows = await conn.fetch("""
                SELECT a.id, a.action, a.service_type, a.details, a.created_at, u.email, u.name
                FROM activity a JOIN users u ON a.user_id = u.id
                ORDER BY a.created_at DESC LIMIT $1 OFFSET $2
            """, per_page, offset)
        return {"success": True, "activity": [dict(r) for r in rows], "total": total, "page": page, "pages": (total + per_page - 1) // per_page}


# ==================== PAYMENTS ====================
@router.get("/payments")
async def admin_payments(request: Request, page: int = 1, per_page: int = 20):
    await _check_admin(request)
    pool = await get_pool()
    async with pool.acquire() as conn:
        offset = (page - 1) * per_page
        total = await conn.fetchval("SELECT COUNT(*) FROM activity WHERE action='payment'")
        rows = await conn.fetch("""
            SELECT a.id, a.details, a.created_at, u.email, u.name, u.total_paid
            FROM activity a JOIN users u ON a.user_id = u.id
            WHERE a.action = 'payment'
            ORDER BY a.created_at DESC LIMIT $1 OFFSET $2
        """, per_page, offset)
        total_revenue = await conn.fetchval("SELECT COALESCE(SUM(total_paid), 0) FROM users")
        month_revenue = await conn.fetchval("""
            SELECT COALESCE(SUM(total_paid), 0) FROM users
            WHERE created_at >= date_trunc('month', CURRENT_DATE)
        """)
        return {
            "success": True,
            "payments": [dict(r) for r in rows],
            "total": total,
            "total_revenue": float(total_revenue),
            "month_revenue": float(month_revenue),
            "page": page,
            "pages": (total + per_page - 1) // per_page
        }


# ==================== PLATFORM SETTINGS ====================
@router.get("/settings")
async def get_settings(request: Request):
    await _check_admin(request)
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Check if settings table exists
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS platform_settings (
                key VARCHAR(100) PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)
        rows = await conn.fetch("SELECT key, value FROM platform_settings")
        settings = {r["key"]: r["value"] for r in rows}
        defaults = {
            "free_brs_limit": settings.get("free_brs_limit", "2"),
            "free_gst_limit": settings.get("free_gst_limit", "1"),
            "free_bookkeeping_limit": settings.get("free_bookkeeping_limit", "1"),
            "brs_price": settings.get("brs_price", "499"),
            "gst_price": settings.get("gst_price", "499"),
            "bookkeeping_price": settings.get("bookkeeping_price", "2999"),
            "tally_push_price": settings.get("tally_push_price", "300"),
            "site_name": settings.get("site_name", "ReconcileAI"),
            "maintenance_mode": settings.get("maintenance_mode", "false"),
            "registration_enabled": settings.get("registration_enabled", "true")
        }
        return {"success": True, "settings": defaults}


class SettingsReq(BaseModel):
    settings: dict


@router.put("/settings")
async def update_settings(req: SettingsReq, request: Request):
    await _check_admin(request)
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS platform_settings (
                key VARCHAR(100) PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)
        for key, value in req.settings.items():
            await conn.execute("""
                INSERT INTO platform_settings (key, value, updated_at)
                VALUES ($1, $2, NOW())
                ON CONFLICT (key) DO UPDATE SET value = $2, updated_at = NOW()
            """, key, str(value))
        return {"success": True, "message": "Settings updated"}


# ==================== EXPORT ====================
@router.get("/export/users")
async def export_users(request: Request):
    await _check_admin(request)
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT id, email, name, firm_name, gstin, phone,
                   free_brs_used, free_gst_used, free_bookkeeping_used,
                   total_reconciliations, total_paid, created_at, last_login
            FROM users ORDER BY created_at DESC
        """)
        csv = "ID,Email,Name,Firm,GSTIN,Phone,BRS Used,GST Used,Book Used,Total Recon,Total Paid,Created,Last Login\n"
        for r in rows:
            csv += f"{r['id']},{r['email']},{r['name'] or ''},{r['firm_name'] or ''},{r['gstin'] or ''},{r['phone'] or ''},{r['free_brs_used']},{r['free_gst_used']},{r['free_bookkeeping_used']},{r['total_reconciliations']},{r['total_paid']},{r['created_at']},{r['last_login'] or ''}\n"
        return Response(content=csv, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=users.csv"})


@router.get("/export/activity")
async def export_activity(request: Request):
    await _check_admin(request)
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT a.id, u.email, a.action, a.service_type, a.details, a.created_at
            FROM activity a JOIN users u ON a.user_id = u.id
            ORDER BY a.created_at DESC
        """)
        csv = "ID,Email,Action,Service,Details,Date\n"
        for r in rows:
            csv += f"{r['id']},{r['email']},{r['action']},{r['service_type'] or ''},{r['details'] or ''},{r['created_at']}\n"
        return Response(content=csv, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=activity.csv"})


# ==================== SYSTEM HEALTH ====================
@router.get("/health")
async def system_health(request: Request):
    await _check_admin(request)
    pool = await get_pool()
    async with pool.acquire() as conn:
        db_ok = await conn.fetchval("SELECT 1")
        users = await conn.fetchval("SELECT COUNT(*) FROM users")
        sessions = await conn.fetchval("SELECT COUNT(*) FROM sessions WHERE expires_at > NOW()")
        expired_sessions = await conn.fetchval("SELECT COUNT(*) FROM sessions WHERE expires_at <= NOW()")
        activities = await conn.fetchval("SELECT COUNT(*) FROM activity")

        # Clean expired sessions
        await conn.execute("DELETE FROM sessions WHERE expires_at <= NOW()")

        return {
            "success": True,
            "health": {
                "database": "connected" if db_ok else "error",
                "total_users": users,
                "active_sessions": sessions,
                "expired_cleaned": expired_sessions,
                "total_activity": activities,
                "server_time": str(datetime.utcnow()),
                "uptime": "running"
            }
        }


@router.post("/maintenance")
async def toggle_maintenance(request: Request):
    await _check_admin(request)
    body = await request.json()
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS platform_settings (
                key VARCHAR(100) PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)
        await conn.execute("""
            INSERT INTO platform_settings (key, value, updated_at)
            VALUES ('maintenance_mode', $1, NOW())
            ON CONFLICT (key) DO UPDATE SET value = $1, updated_at = NOW()
        """, str(body.get("enabled", False)).lower())
        return {"success": True, "message": f"Maintenance mode: {body.get('enabled', False)}"}
