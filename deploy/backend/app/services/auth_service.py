import sqlite3
import hashlib
import secrets
import os
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent.parent.parent / "data" / "users.db"

PBKDF2_ITERATIONS = 100000
SESSION_EXPIRY_HOURS = 720  # 30 days


def get_db():
    os.makedirs(str(DB_PATH.parent), exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            firm_name TEXT DEFAULT '',
            gstin TEXT DEFAULT '',
            phone TEXT DEFAULT '',
            role TEXT DEFAULT 'user',
            free_brs_used INTEGER DEFAULT 0,
            free_gst_used INTEGER DEFAULT 0,
            free_bookkeeping_used INTEGER DEFAULT 0,
            total_reconciliations INTEGER DEFAULT 0,
            total_paid INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now')),
            last_login TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token TEXT UNIQUE NOT NULL,
            created_at TEXT DEFAULT (datetime('now')),
            expires_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS user_activity (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            service_type TEXT DEFAULT '',
            details TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
    """)
    conn.commit()
    conn.close()
    logger.info("Auth database initialized")


def hash_password(password: str, salt: str = None) -> tuple:
    if salt is None:
        salt = secrets.token_hex(32)
    password_hash = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        PBKDF2_ITERATIONS
    ).hex()
    return password_hash, salt


def verify_password(password: str, stored_hash: str, salt: str) -> bool:
    password_hash, _ = hash_password(password, salt)
    return secrets.compare_digest(password_hash, stored_hash)


def register_user(name: str, email: str, password: str,
                  firm_name: str = "", gstin: str = "",
                  phone: str = "") -> Dict:
    conn = get_db()
    try:
        existing = conn.execute(
            "SELECT id FROM users WHERE email = ?", (email.lower(),)
        ).fetchone()
        if existing:
            return {"success": False, "error": "Email already registered"}

        password_hash, salt = hash_password(password)

        cursor = conn.execute(
            """INSERT INTO users (name, email, password_hash, salt,
               firm_name, gstin, phone) VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (name, email.lower(), password_hash, salt,
             firm_name, gstin, phone)
        )
        user_id = cursor.lastrowid
        conn.commit()

        token = create_session(user_id)

        logger.info(f"User registered: {email}")
        return {
            "success": True,
            "user_id": user_id,
            "token": token,
            "name": name,
            "email": email.lower(),
        }
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return {"success": False, "error": str(e)}
    finally:
        conn.close()


def login_user(email: str, password: str) -> Dict:
    conn = get_db()
    try:
        user = conn.execute(
            "SELECT * FROM users WHERE email = ?", (email.lower(),)
        ).fetchone()

        if not user:
            return {"success": False, "error": "Email not found"}

        if not verify_password(password, user['password_hash'], user['salt']):
            return {"success": False, "error": "Incorrect password"}

        token = create_session(user['id'])

        conn.execute(
            "UPDATE users SET last_login = datetime('now') WHERE id = ?",
            (user['id'],)
        )
        conn.commit()

        logger.info(f"User logged in: {email}")
        return {
            "success": True,
            "user_id": user['id'],
            "token": token,
            "name": user['name'],
            "email": user['email'],
            "firm_name": user['firm_name'],
            "gstin": user['gstin'],
            "role": user['role'],
        }
    except Exception as e:
        logger.error(f"Login error: {e}")
        return {"success": False, "error": str(e)}
    finally:
        conn.close()


def create_session(user_id: int) -> str:
    conn = get_db()
    token = secrets.token_hex(48)
    expires_at = (
        datetime.utcnow() + timedelta(hours=SESSION_EXPIRY_HOURS)
    ).isoformat()
    conn.execute(
        "INSERT INTO sessions (user_id, token, expires_at) VALUES (?, ?, ?)",
        (user_id, token, expires_at)
    )
    conn.commit()
    conn.close()
    return token


def validate_session(token: str) -> Optional[Dict]:
    if not token:
        return None
    conn = get_db()
    try:
        session = conn.execute(
            """SELECT s.user_id, s.expires_at, u.name, u.email,
               u.firm_name, u.gstin, u.role, u.phone,
               u.free_brs_used, u.free_gst_used,
               u.free_bookkeeping_used, u.total_reconciliations,
               u.total_paid
               FROM sessions s JOIN users u ON s.user_id = u.id
               WHERE s.token = ?""",
            (token,)
        ).fetchone()

        if not session:
            return None

        expires = datetime.fromisoformat(session['expires_at'])
        if datetime.utcnow() > expires:
            conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
            conn.commit()
            return None

        return dict(session)
    except Exception as e:
        logger.error(f"Session validation error: {e}")
        return None
    finally:
        conn.close()


def logout_user(token: str) -> bool:
    conn = get_db()
    try:
        conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()


def get_user_profile(user_id: int) -> Optional[Dict]:
    conn = get_db()
    try:
        user = conn.execute(
            """SELECT id, name, email, firm_name, gstin, phone, role,
               free_brs_used, free_gst_used, free_bookkeeping_used,
               total_reconciliations, total_paid,
               created_at, last_login
               FROM users WHERE id = ?""",
            (user_id,)
        ).fetchone()
        return dict(user) if user else None
    except Exception as e:
        logger.error(f"Profile error: {e}")
        return None
    finally:
        conn.close()


def update_profile(user_id: int, name: str = None,
                   firm_name: str = None, gstin: str = None,
                   phone: str = None) -> bool:
    conn = get_db()
    try:
        updates = []
        params = []
        if name is not None:
            updates.append("name = ?")
            params.append(name)
        if firm_name is not None:
            updates.append("firm_name = ?")
            params.append(firm_name)
        if gstin is not None:
            updates.append("gstin = ?")
            params.append(gstin)
        if phone is not None:
            updates.append("phone = ?")
            params.append(phone)

        if not updates:
            return False

        params.append(user_id)
        conn.execute(
            f"UPDATE users SET {', '.join(updates)} WHERE id = ?",
            params
        )
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Profile update error: {e}")
        return False
    finally:
        conn.close()


def change_password(user_id: int, old_password: str,
                    new_password: str) -> Dict:
    conn = get_db()
    try:
        user = conn.execute(
            "SELECT password_hash, salt FROM users WHERE id = ?",
            (user_id,)
        ).fetchone()

        if not user:
            return {"success": False, "error": "User not found"}

        if not verify_password(old_password, user['password_hash'],
                               user['salt']):
            return {"success": False, "error": "Incorrect old password"}

        new_hash, new_salt = hash_password(new_password)
        conn.execute(
            "UPDATE users SET password_hash = ?, salt = ? WHERE id = ?",
            (new_hash, new_salt, user_id)
        )
        conn.commit()
        return {"success": True}
    except Exception as e:
        logger.error(f"Password change error: {e}")
        return {"success": False, "error": str(e)}
    finally:
        conn.close()


def record_activity(user_id: int, action: str,
                    service_type: str = "", details: str = ""):
    conn = get_db()
    try:
        conn.execute(
            """INSERT INTO user_activity (user_id, action, service_type,
               details) VALUES (?, ?, ?, ?)""",
            (user_id, action, service_type, details)
        )
        conn.commit()
    except Exception as e:
        logger.error(f"Activity record error: {e}")
    finally:
        conn.close()


def get_user_activity(user_id: int, limit: int = 50) -> list:
    conn = get_db()
    try:
        rows = conn.execute(
            """SELECT action, service_type, details, created_at
               FROM user_activity WHERE user_id = ?
               ORDER BY created_at DESC LIMIT ?""",
            (user_id, limit)
        ).fetchall()
        return [dict(r) for r in rows]
    except Exception as e:
        logger.error(f"Activity fetch error: {e}")
        return []
    finally:
        conn.close()


def increment_free_usage(user_id: int, service: str):
    conn = get_db()
    try:
        col = f"free_{service}_used"
        conn.execute(
            f"UPDATE users SET {col} = {col} + 1, "
            f"total_reconciliations = total_reconciliations + 1 "
            f"WHERE id = ?",
            (user_id,)
        )
        conn.commit()
    except Exception as e:
        logger.error(f"Usage increment error: {e}")
    finally:
        conn.close()


def get_dashboard_stats(user_id: int) -> Dict:
    conn = get_db()
    try:
        user = conn.execute(
            """SELECT name, firm_name, created_at, last_login,
               free_brs_used, free_gst_used, free_bookkeeping_used,
               total_reconciliations, total_paid
               FROM users WHERE id = ?""",
            (user_id,)
        ).fetchone()

        if not user:
            return {}

        activity_count = conn.execute(
            "SELECT COUNT(*) as cnt FROM user_activity WHERE user_id = ?",
            (user_id,)
        ).fetchone()

        return {
            "name": user['name'],
            "firm_name": user['firm_name'],
            "member_since": user['created_at'],
            "last_login": user['last_login'],
            "usage": {
                "free_brs_used": user['free_brs_used'],
                "free_gst_used": user['free_gst_used'],
                "free_bookkeeping_used": user['free_bookkeeping_used'],
                "total_reconciliations": user['total_reconciliations'],
                "total_paid": user['total_paid'],
                "activities": activity_count['cnt'],
            },
            "free_tier": {
                "brs_remaining": max(0, 2 - user['free_brs_used']),
                "gst_remaining": max(0, 1 - user['free_gst_used']),
                "bookkeeping_remaining": max(0, 1 - user['free_bookkeeping_used']),
            }
        }
    except Exception as e:
        logger.error(f"Dashboard stats error: {e}")
        return {}
    finally:
        conn.close()


# Initialize on import
init_db()
