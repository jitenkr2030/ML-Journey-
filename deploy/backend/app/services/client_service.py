import asyncpg
from asyncpg.pool import Pool
from typing import Optional, List
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)

_pool: Optional[Pool] = None

async def get_client_pool() -> Pool:
    global _pool
    if _pool is None:
        url = os.getenv("DATABASE_URL", "")
        if not url:
            raise ValueError("DATABASE_URL not set")
        _pool = await asyncpg.create_pool(url, min_size=1, max_size=5, ssl='require')
        await _create_tables(_pool)
        logger.info("Client database initialized")
    return _pool

async def _create_tables(pool: Pool):
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS clients (
                id SERIAL PRIMARY KEY,
                user_email TEXT NOT NULL,
                name TEXT NOT NULL,
                gstin TEXT DEFAULT '',
                pan TEXT DEFAULT '',
                email TEXT DEFAULT '',
                phone TEXT DEFAULT '',
                address TEXT DEFAULT '',
                notes TEXT DEFAULT '',
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)
        logger.info("Clients table ready")

async def add_client(user_email: str, data: dict) -> dict:
    try:
        pool = await get_client_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """INSERT INTO clients (user_email, name, gstin, pan, email, phone, address, notes)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8) RETURNING *""",
                user_email,
                data.get("name", ""),
                data.get("gstin", "").upper(),
                data.get("pan", "").upper(),
                data.get("email", ""),
                data.get("phone", ""),
                data.get("address", ""),
                data.get("notes", ""),
            )
            logger.info(f"Client added: {data.get('name')} for {user_email}")
            return _row_to_dict(row)
    except Exception as e:
        logger.error(f"Failed to add client: {e}")
        raise

async def update_client(client_id: int, user_email: str, data: dict) -> dict:
    try:
        pool = await get_client_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """UPDATE clients SET name=$1, gstin=$2, pan=$3, email=$4,
                   phone=$5, address=$6, notes=$7, updated_at=NOW()
                   WHERE id=$8 AND user_email=$9 RETURNING *""",
                data.get("name", ""),
                data.get("gstin", "").upper(),
                data.get("pan", "").upper(),
                data.get("email", ""),
                data.get("phone", ""),
                data.get("address", ""),
                data.get("notes", ""),
                client_id,
                user_email,
            )
            if not row:
                raise ValueError("Client not found")
            logger.info(f"Client updated: id={client_id}")
            return _row_to_dict(row)
    except Exception as e:
        logger.error(f"Failed to update client: {e}")
        raise

async def delete_client(client_id: int, user_email: str) -> bool:
    try:
        pool = await get_client_pool()
        async with pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM clients WHERE id = $1 AND user_email = $2",
                client_id, user_email
            )
            deleted = "1" in result
            if deleted:
                logger.info(f"Client deleted: id={client_id}")
            return deleted
    except Exception as e:
        logger.error(f"Failed to delete client: {e}")
        return False

async def list_clients(user_email: str, status: str = "") -> List[dict]:
    try:
        pool = await get_client_pool()
        async with pool.acquire() as conn:
            if status:
                rows = await conn.fetch(
                    """SELECT * FROM clients WHERE user_email = $1 AND status = $2
                       ORDER BY name ASC""",
                    user_email, status
                )
            else:
                rows = await conn.fetch(
                    """SELECT * FROM clients WHERE user_email = $1
                       ORDER BY name ASC""",
                    user_email
                )
            return [_row_to_dict(r) for r in rows]
    except Exception as e:
        logger.error(f"Failed to list clients: {e}")
        return []

async def get_client(client_id: int, user_email: str) -> Optional[dict]:
    try:
        pool = await get_client_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM clients WHERE id = $1 AND user_email = $2",
                client_id, user_email
            )
            return _row_to_dict(row) if row else None
    except Exception as e:
        logger.error(f"Failed to get client: {e}")
        return None

async def search_clients(user_email: str, query: str) -> List[dict]:
    try:
        pool = await get_client_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """SELECT * FROM clients
                   WHERE user_email = $1
                   AND (name ILIKE $2 OR gstin ILIKE $2 OR pan ILIKE $2)
                   ORDER BY name ASC LIMIT 20""",
                user_email, f"%{query}%"
            )
            return [_row_to_dict(r) for r in rows]
    except Exception as e:
        logger.error(f"Failed to search clients: {e}")
        return []

def _row_to_dict(row) -> dict:
    return {
        "id": row["id"],
        "name": row["name"],
        "gstin": row["gstin"],
        "pan": row["pan"],
        "email": row["email"],
        "phone": row["phone"],
        "address": row["address"],
        "notes": row["notes"],
        "status": row["status"],
        "created_at": row["created_at"].strftime("%Y-%m-%d %H:%M") if row["created_at"] else "",
        "updated_at": row["updated_at"].strftime("%Y-%m-%d %H:%M") if row["updated_at"] else "",
    }
