import asyncpg
from asyncpg.pool import Pool
from typing import Optional, List
import logging
import os
import json
from datetime import datetime

logger = logging.getLogger(__name__)

_pool: Optional[Pool] = None

async def get_history_pool() -> Pool:
    global _pool
    if _pool is None:
        url = os.getenv("DATABASE_URL", "")
        if not url:
            raise ValueError("DATABASE_URL not set")
        _pool = await asyncpg.create_pool(url, min_size=1, max_size=5, ssl='require')
        await _create_tables(_pool)
        logger.info("History database initialized")
    return _pool

async def _create_tables(pool: Pool):
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id SERIAL PRIMARY KEY,
                user_email TEXT NOT NULL DEFAULT 'anonymous',
                recon_type TEXT NOT NULL,
                total_transactions INTEGER DEFAULT 0,
                matched_count INTEGER DEFAULT 0,
                unmatched_count INTEGER DEFAULT 0,
                match_rate REAL DEFAULT 0,
                summary TEXT DEFAULT '{}',
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        logger.info("History table ready")

async def save_history(user_email: str, recon_type: str, result: dict) -> int:
    try:
        pool = await get_history_pool()
        summary = {
            "total_transactions": result.get("total_transactions", 0),
            "matched_count": result.get("matched_count", 0),
            "unmatched_count": result.get("unmatched_count", 0),
            "match_rate": result.get("match_rate", 0),
        }
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """INSERT INTO history (user_email, recon_type, total_transactions,
                   matched_count, unmatched_count, match_rate, summary)
                   VALUES ($1, $2, $3, $4, $5, $6, $7) RETURNING id""",
                user_email,
                recon_type,
                result.get("total_transactions", 0),
                result.get("matched_count", 0),
                result.get("unmatched_count", 0),
                result.get("match_rate", 0),
                json.dumps(summary),
            )
            hid = row["id"]
            logger.info(f"History saved: {recon_type} for {user_email} (id={hid})")
            return hid
    except Exception as e:
        logger.error(f"Failed to save history: {e}")
        return -1

async def get_history_list(user_email: str, limit: int = 20) -> List[dict]:
    try:
        pool = await get_history_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """SELECT id, recon_type, total_transactions, matched_count,
                   unmatched_count, match_rate, summary, created_at
                   FROM history WHERE user_email = $1
                   ORDER BY created_at DESC LIMIT $2""",
                user_email, limit
            )
            return [
                {
                    "id": r["id"],
                    "recon_type": r["recon_type"],
                    "total_transactions": r["total_transactions"],
                    "matched_count": r["matched_count"],
                    "unmatched_count": r["unmatched_count"],
                    "match_rate": r["match_rate"],
                    "created_at": r["created_at"].strftime("%Y-%m-%d %H:%M") if r["created_at"] else "",
                }
                for r in rows
            ]
    except Exception as e:
        logger.error(f"Failed to get history: {e}")
        return []

async def delete_history_entry(history_id: int, user_email: str) -> bool:
    try:
        pool = await get_history_pool()
        async with pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM history WHERE id = $1 AND user_email = $2",
                history_id, user_email
            )
            return "1" in result
    except Exception as e:
        logger.error(f"Failed to delete history: {e}")
        return False

async def get_stats(user_email: str) -> dict:
    try:
        pool = await get_history_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """SELECT COUNT(*) as total,
                   SUM(CASE WHEN recon_type = 'brs' THEN 1 ELSE 0 END) as brs_count,
                   SUM(CASE WHEN recon_type = 'gst' THEN 1 ELSE 0 END) as gst_count,
                   SUM(CASE WHEN recon_type = 'upi' THEN 1 ELSE 0 END) as upi_count,
                   SUM(CASE WHEN recon_type = 'bookkeeping' THEN 1 ELSE 0 END) as bk_count
                   FROM history WHERE user_email = $1""",
                user_email
            )
            return {
                "total": row["total"] or 0,
                "brs": row["brs_count"] or 0,
                "gst": row["gst_count"] or 0,
                "upi": row["upi_count"] or 0,
                "bookkeeping": row["bk_count"] or 0,
            }
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        return {"total": 0, "brs": 0, "gst": 0, "upi": 0, "bookkeeping": 0}
