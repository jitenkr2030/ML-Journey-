import asyncpg
from asyncpg.pool import Pool
from typing import Optional, List
import logging
import os

logger = logging.getLogger(__name__)

_pool: Optional[Pool] = None

async def get_inquiry_pool() -> Pool:
    global _pool
    if _pool is None:
        url = os.getenv("DATABASE_URL", "")
        if not url:
            raise ValueError("DATABASE_URL not set")
        _pool = await asyncpg.create_pool(url, min_size=1, max_size=5, ssl='require')
        await _create_tables(_pool)
        logger.info("Service inquiry database initialized")
    return _pool

async def _create_tables(pool: Pool):
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS service_inquiries (
                id SERIAL PRIMARY KEY,
                service_type TEXT NOT NULL DEFAULT 'manual_accounting',
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                phone TEXT DEFAULT '',
                company TEXT DEFAULT '',
                gstin TEXT DEFAULT '',
                city TEXT DEFAULT '',
                message TEXT DEFAULT '',
                preferred_time TEXT DEFAULT '',
                status TEXT DEFAULT 'new',
                notes TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)
        logger.info("Service inquiries table ready")

async def create_inquiry(data: dict) -> dict:
    try:
        pool = await get_inquiry_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """INSERT INTO service_inquiries
                   (service_type, name, email, phone, company, gstin, city, message, preferred_time)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9) RETURNING *""",
                data.get("service_type", "manual_accounting"),
                data.get("name", ""),
                data.get("email", ""),
                data.get("phone", ""),
                data.get("company", ""),
                data.get("gstin", "").upper(),
                data.get("city", ""),
                data.get("message", ""),
                data.get("preferred_time", ""),
            )
            logger.info(f"Service inquiry created: {data.get('name')} ({data.get('email')})")
            return _row_to_dict(row)
    except Exception as e:
        logger.error(f"Failed to create inquiry: {e}")
        raise

async def list_inquiries(status: str = "") -> List[dict]:
    try:
        pool = await get_inquiry_pool()
        async with pool.acquire() as conn:
            if status:
                rows = await conn.fetch(
                    """SELECT * FROM service_inquiries WHERE status = $1
                       ORDER BY created_at DESC LIMIT 100""",
                    status
                )
            else:
                rows = await conn.fetch(
                    "SELECT * FROM service_inquiries ORDER BY created_at DESC LIMIT 100"
                )
            return [_row_to_dict(r) for r in rows]
    except Exception as e:
        logger.error(f"Failed to list inquiries: {e}")
        return []

async def update_inquiry_status(inquiry_id: int, status: str, notes: str = "") -> bool:
    try:
        pool = await get_inquiry_pool()
        async with pool.acquire() as conn:
            result = await conn.execute(
                """UPDATE service_inquiries
                   SET status = $1, notes = $2, updated_at = NOW()
                   WHERE id = $3""",
                status, notes, inquiry_id
            )
            return "1" in result
    except Exception as e:
        logger.error(f"Failed to update inquiry: {e}")
        return False

async def get_inquiry_stats() -> dict:
    try:
        pool = await get_inquiry_pool()
        async with pool.acquire() as conn:
            total = await conn.fetchval("SELECT COUNT(*) FROM service_inquiries")
            new = await conn.fetchval("SELECT COUNT(*) FROM service_inquiries WHERE status = 'new'")
            contacted = await conn.fetchval("SELECT COUNT(*) FROM service_inquiries WHERE status = 'contacted'")
            converted = await conn.fetchval("SELECT COUNT(*) FROM service_inquiries WHERE status = 'converted'")
            return {"total": total, "new": new, "contacted": contacted, "converted": converted}
    except Exception as e:
        logger.error(f"Failed to get inquiry stats: {e}")
        return {"total": 0, "new": 0, "contacted": 0, "converted": 0}

def _row_to_dict(row) -> dict:
    return {
        "id": row["id"],
        "service_type": row["service_type"],
        "name": row["name"],
        "email": row["email"],
        "phone": row["phone"],
        "company": row["company"],
        "gstin": row["gstin"],
        "city": row["city"],
        "message": row["message"],
        "preferred_time": row["preferred_time"],
        "status": row["status"],
        "notes": row["notes"],
        "created_at": row["created_at"].strftime("%Y-%m-%d %H:%M") if row["created_at"] else "",
        "updated_at": row["updated_at"].strftime("%Y-%m-%d %H:%M") if row["updated_at"] else "",
    }
