import asyncpg
from asyncpg.pool import Pool
from typing import Optional, Dict
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)

_pool: Optional[Pool] = None

FREE_LIMITS = {
    "brs": 2,
    "gst": 1,
    "upi": 1,
    "gstr1": 0,
    "gstr2b": 0,
    "gstr3b": 0,
    "bookkeeping": 0,
}

async def get_usage_pool() -> Pool:
    global _pool
    if _pool is None:
        url = os.getenv("DATABASE_URL", "")
        if not url:
            raise ValueError("DATABASE_URL not set")
        _pool = await asyncpg.create_pool(url, min_size=1, max_size=5, ssl='require')
        await _create_tables(_pool)
        logger.info("Usage database initialized")
    return _pool

async def _create_tables(pool: Pool):
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS usage_tracking (
                id SERIAL PRIMARY KEY,
                user_email TEXT NOT NULL,
                recon_type TEXT NOT NULL,
                usage_month TEXT NOT NULL,
                used_count INTEGER DEFAULT 0,
                UNIQUE(user_email, recon_type, usage_month)
            )
        """)
        logger.info("Usage tracking table ready")

def _current_month() -> str:
    now = datetime.utcnow()
    return f"{now.year}-{now.month:02d}"

async def check_limit(user_email: str, recon_type: str) -> Dict:
    try:
        pool = await get_usage_pool()
        month = _current_month()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """SELECT used_count FROM usage_tracking
                   WHERE user_email=$1 AND recon_type=$2 AND usage_month=$3""",
                user_email, recon_type, month
            )
            used = row["used_count"] if row else 0
            limit = FREE_LIMITS.get(recon_type, 0)
            remaining = max(0, limit - used)

            return {
                "allowed": remaining > 0 or limit == 0,
                "recon_type": recon_type,
                "used": used,
                "limit": limit,
                "remaining": remaining,
                "month": month,
                "is_paid_type": limit == 0,
            }
    except Exception as e:
        logger.error(f"Failed to check limit: {e}")
        return {"allowed": True, "used": 0, "limit": 0, "remaining": 0, "error": str(e)}

async def consume_usage(user_email: str, recon_type: str) -> Dict:
    try:
        pool = await get_usage_pool()
        month = _current_month()
        async with pool.acquire() as conn:
            await conn.execute(
                """INSERT INTO usage_tracking (user_email, recon_type, usage_month, used_count)
                   VALUES ($1, $2, $3, 1)
                   ON CONFLICT (user_email, recon_type, usage_month)
                   DO UPDATE SET used_count = usage_tracking.used_count + 1""",
                user_email, recon_type, month
            )
            row = await conn.fetchrow(
                """SELECT used_count FROM usage_tracking
                   WHERE user_email=$1 AND recon_type=$2 AND usage_month=$3""",
                user_email, recon_type, month
            )
            used = row["used_count"] if row else 1
            limit = FREE_LIMITS.get(recon_type, 0)
            remaining = max(0, limit - used)
            logger.info(f"Usage consumed: {recon_type} for {user_email} ({used}/{limit})")
            return {
                "used": used,
                "limit": limit,
                "remaining": remaining,
                "month": month,
            }
    except Exception as e:
        logger.error(f"Failed to consume usage: {e}")
        return {"used": 0, "limit": 0, "remaining": 0, "error": str(e)}

async def get_usage_status(user_email: str) -> Dict:
    try:
        pool = await get_usage_pool()
        month = _current_month()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """SELECT recon_type, used_count FROM usage_tracking
                   WHERE user_email=$1 AND usage_month=$2""",
                user_email, month
            )
            used_map = {r["recon_type"]: r["used_count"] for r in rows}
            status = {}
            for rt, limit in FREE_LIMITS.items():
                used = used_map.get(rt, 0)
                status[rt] = {
                    "used": used,
                    "limit": limit,
                    "remaining": max(0, limit - used),
                }
            return {"month": month, "usage": status}
    except Exception as e:
        logger.error(f"Failed to get usage status: {e}")
        return {"month": _current_month(), "usage": {}}
