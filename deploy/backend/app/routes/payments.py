import sqlite3
import os
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

DB_PATH = '/data/payments.db'
ADMIN_KEY = "reconcile2026"


def get_db():
    os.makedirs(os.path.dirname(DB_PATH = '/data/payments.db'
    conn = sqlite3.connect(DB_PATH = '/data/payments.db'
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT UNIQUE NOT NULL,
            utr TEXT NOT NULL,
            amount REAL DEFAULT 500,
            status TEXT DEFAULT 'pending',
            total_transactions INTEGER DEFAULT 0,
            matched_count INTEGER DEFAULT 0,
            unmatched_count INTEGER DEFAULT 0,
            match_rate REAL DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            verified_at TEXT
        )
    """)
    conn.commit()
    conn.close()


init_db()


# ===== SCHEMAS =====

class PaymentSubmit(BaseModel):
    session_id: str
    utr: str
    amount: float = 500
    total_transactions: int = 0
    matched_count: int = 0
    unmatched_count: int = 0
    match_rate: float = 0


# ===== PUBLIC ENDPOINTS =====

@router.post("/api/payment/submit")
async def submit_payment(data: PaymentSubmit):
    utr = data.utr.strip()
    if len(utr) < 10:
        raise HTTPException(status_code=400, detail="UTR must be at least 10 characters")

    conn = get_db()
    try:
        existing = conn.execute(
            "SELECT * FROM payments WHERE session_id = ?",
            (data.session_id,)
        ).fetchone()

        if existing:
            if existing["status"] == "verified":
                return {"status": "already_verified"}
            conn.execute(
                """UPDATE payments SET utr = ?, total_transactions = ?,
                   matched_count = ?, unmatched_count = ?, match_rate = ?
                   WHERE session_id = ?""",
                (utr, data.total_transactions, data.matched_count,
                 data.unmatched_count, data.match_rate, data.session_id)
            )
        else:
            conn.execute(
                """INSERT INTO payments
                   (session_id, utr, amount, total_transactions,
                    matched_count, unmatched_count, match_rate)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (data.session_id, utr, data.amount,
                 data.total_transactions, data.matched_count,
                 data.unmatched_count, data.match_rate)
            )
        conn.commit()
        return {
            "status": "submitted",
            "message": "UTR submitted. Verification takes 5-30 minutes."
        }
    finally:
        conn.close()


@router.get("/api/payment/status/{session_id}")
async def payment_status(session_id: str):
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT status FROM payments WHERE session_id = ?",
            (session_id,)
        ).fetchone()
        if not row:
            return {"status": "not_found"}
        return {"status": row["status"]}
    finally:
        conn.close()


# ===== ADMIN ENDPOINTS =====

@router.get("/api/admin/payments")
async def list_payments(key: str = ""):
    if key != ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Invalid admin key")
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT * FROM payments ORDER BY created_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


@router.post("/api/admin/verify/{payment_id}")
async def verify_payment(payment_id: int, key: str = ""):
    if key != ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Invalid admin key")
    conn = get_db()
    try:
        conn.execute(
            "UPDATE payments SET status = 'verified', verified_at = ? WHERE id = ?",
            (datetime.now().isoformat(), payment_id)
        )
        conn.commit()
        return {"status": "verified"}
    finally:
        conn.close()


@router.post("/api/admin/reject/{payment_id}")
async def reject_payment(payment_id: int, key: str = ""):
    if key != ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Invalid admin key")
    conn = get_db()
    try:
        conn.execute(
            "UPDATE payments SET status = 'rejected' WHERE id = ?",
            (payment_id,)
        )
        conn.commit()
        return {"status": "rejected"}
    finally:
        conn.close()
