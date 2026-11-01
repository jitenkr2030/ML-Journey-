import hashlib
import secrets
import os
import logging
from datetime import datetime, timedelta
from typing import Optional
from dotenv import load_dotenv
load_dotenv()
import asyncpg
from asyncpg.pool import Pool

logger = logging.getLogger(__name__)
_pool: Optional[Pool] = None

async def get_pool() -> Pool:
    global _pool
    if _pool is None:
        url = os.getenv("DATABASE_URL", "")
        if not url:
            raise ValueError("DATABASE_URL not set in .env")
        _pool = await asyncpg.create_pool(url, min_size=1, max_size=5, ssl='require')
        await _create_tables(_pool)
        logger.info("Auth database initialized (PostgreSQL/Aiven)")
    return _pool

async def _create_tables(pool: Pool):
    async with pool.acquire() as conn:
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                name VARCHAR(100),
                firm_name VARCHAR(200),
                gstin VARCHAR(20),
                phone VARCHAR(20),
                is_admin BOOLEAN DEFAULT FALSE,
                free_brs_used INTEGER DEFAULT 0,
                free_gst_used INTEGER DEFAULT 0,
                free_bookkeeping_used INTEGER DEFAULT 0,
                total_reconciliations INTEGER DEFAULT 0,
                total_paid INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT NOW(),
                last_login TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS sessions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                token VARCHAR(255) UNIQUE NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT NOW()
            );
            CREATE TABLE IF NOT EXISTS activity (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                action VARCHAR(50),
                service_type VARCHAR(50),
                details TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            );
        ''')

def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex()
    return f"{salt}:{h}"

def verify_password(password: str, stored: str) -> bool:
    try:
        salt, h = stored.split(':')
        return hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex() == h
    except:
        return False

def generate_token() -> str:
    return secrets.token_urlsafe(32)

async def register_user(email: str, password: str, name: str, firm_name: str = "", gstin: str = "", phone: str = "") -> dict:
    pool = await get_pool()
    async with pool.acquire() as conn:
        existing = await conn.fetchrow("SELECT id FROM users WHERE email = $1", email)
        if existing:
            return {"success": False, "detail": "Email already registered"}
        pw = hash_password(password)
        row = await conn.fetchrow(
            "INSERT INTO users (email,password_hash,name,firm_name,gstin,phone) VALUES ($1,$2,$3,$4,$5,$6) RETURNING id",
            email, pw, name, firm_name, gstin, phone
        )
        uid = row['id']
        token = generate_token()
        exp = datetime.utcnow() + timedelta(days=30)
        await conn.execute("INSERT INTO sessions(user_id,token,expires_at) VALUES($1,$2,$3)", uid, token, exp)
        await conn.execute("INSERT INTO activity(user_id,action,service_type,details) VALUES($1,'register','auth','New account created')", uid)
        return {"success": True, "token": token, "user": {"id": uid, "email": email, "name": name, "firm_name": firm_name}}

async def login_user(email: str, password: str) -> dict:
    pool = await get_pool()
    async with pool.acquire() as conn:
        u = await conn.fetchrow("SELECT * FROM users WHERE email = $1", email)
        if not u or not verify_password(password, u['password_hash']):
            return {"success": False, "detail": "Invalid email or password"}
        token = generate_token()
        exp = datetime.utcnow() + timedelta(days=30)
        await conn.execute("INSERT INTO sessions(user_id,token,expires_at) VALUES($1,$2,$3)", u['id'], token, exp)
        await conn.execute("UPDATE users SET last_login=NOW() WHERE id=$1", u['id'])
        await conn.execute("INSERT INTO activity(user_id,action,service_type,details) VALUES($1,'login','auth','Successful login')", u['id'])
        return {"success": True, "token": token, "user": {"id": u['id'], "email": u['email'], "name": u['name'], "firm_name": u['firm_name']}}

async def get_user_by_token(token: str) -> Optional[dict]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        r = await conn.fetchrow("""
            SELECT u.id,u.email,u.name,u.firm_name,u.gstin,u.phone,
                   u.free_brs_used,u.free_gst_used,u.free_bookkeeping_used,
                   u.total_reconciliations,u.total_paid,u.created_at,u.last_login
            FROM users u JOIN sessions s ON u.id=s.user_id
            WHERE s.token=$1 AND s.expires_at>NOW()
        """, token)
        return dict(r) if r else None

async def logout_user(token: str) -> bool:
    pool = await get_pool()
    async with pool.acquire() as conn:
        r = await conn.execute("DELETE FROM sessions WHERE token=$1", token)
        return "DELETE 1" in r

async def get_dashboard_stats(user_id: int) -> dict:
    pool = await get_pool()
    async with pool.acquire() as conn:
        u = await conn.fetchrow("""
            SELECT free_brs_used,free_gst_used,free_bookkeeping_used,
                   total_reconciliations,total_paid,created_at,last_login,name
            FROM users WHERE id=$1
        """, user_id)
        if not u:
            return {"success": False}
        u = dict(u)
        ac = await conn.fetchval("SELECT COUNT(*) FROM activity WHERE user_id=$1", user_id)
        return {"success": True, "stats": {
            "usage": {
                "free_brs_used": u['free_brs_used'],
                "free_gst_used": u['free_gst_used'],
                "free_bookkeeping_used": u['free_bookkeeping_used'],
                "total_reconciliations": u['total_reconciliations'],
                "total_paid": u['total_paid'],
                "activities": ac or 0
            },
            "free_tier": {
                "brs_remaining": max(0, 2 - (u['free_brs_used'] or 0)),
                "gst_remaining": max(0, 1 - (u['free_gst_used'] or 0)),
                "bookkeeping_remaining": max(0, 1 - (u['free_bookkeeping_used'] or 0)),
            },
            "name": u['name'],
            "member_since": str(u['created_at'] or ''),
            "last_login": str(u['last_login'] or '')
        }}

async def get_activity(user_id: int) -> list:
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT action,service_type,details,created_at FROM activity WHERE user_id=$1 ORDER BY created_at DESC LIMIT 50",
            user_id
        )
        return [dict(r) for r in rows]

async def update_profile(user_id: int, name: str, firm_name: str, gstin: str, phone: str) -> dict:
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("UPDATE users SET name=$1,firm_name=$2,gstin=$3,phone=$4 WHERE id=$5", name, firm_name, gstin, phone, user_id)
        await conn.execute("INSERT INTO activity(user_id,action,service_type,details) VALUES($1,'update_profile','auth','Profile updated')", user_id)
        return {"success": True}

async def change_password(user_id: int, old_password: str, new_password: str) -> dict:
    pool = await get_pool()
    async with pool.acquire() as conn:
        u = await conn.fetchrow("SELECT password_hash FROM users WHERE id=$1", user_id)
        if not u or not verify_password(old_password, u['password_hash']):
            return {"success": False, "detail": "Old password is incorrect"}
        await conn.execute("UPDATE users SET password_hash=$1 WHERE id=$2", hash_password(new_password), user_id)
        await conn.execute("INSERT INTO activity(user_id,action,service_type,details) VALUES($1,'change_password','auth','Password changed')", user_id)
        return {"success": True}

async def init_auth_db():
    await get_pool()
    logger.info("Auth database initialized (PostgreSQL/Aiven)")


# Compatibility alias for dashboard routes
async def validate_session(token: str):
    return await get_user_by_token(token)


# Compatibility alias
async def get_user_activity(user_id: int):
    return await get_activity(user_id)


async def create_admin_user():
    """Create default admin account if not exists"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Add is_admin column if missing
        try:
            await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT FALSE")
        except:
            pass

        existing = await conn.fetchrow("SELECT id FROM users WHERE email = $1", "admin@reconcileai.com")
        if existing:
            await conn.execute("UPDATE users SET is_admin = TRUE WHERE email = $1", "admin@reconcileai.com")
            logger.info("Admin user already exists, set is_admin=True")
            return

        pw = hash_password("Admin@2026!")
        await conn.execute(
            "INSERT INTO users (email, password_hash, name, is_admin) VALUES ($1, $2, $3, $4)",
            "admin@reconcileai.com", pw, "Admin", True
        )
        logger.info("Admin user created: admin@reconcileai.com")

async def is_user_admin(user_id: int) -> bool:
    pool = await get_pool()
    async with pool.acquire() as conn:
        val = await conn.fetchval("SELECT is_admin FROM users WHERE id = $1", user_id)
        return bool(val)
