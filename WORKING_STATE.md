# WORKING STATE - Saved on 2026-11-14

## Login Credentials
- Email:    admin@reconcileai.com
- Password: Reconcile@2026

## What's Working
1. Login page (both old + new modal)
2. Dashboard redirect after login
3. All pages: /, /tools, /faq, /compare, /extensions, /config
4. Scanner blocking (404 for .zip, .sql, .bak etc)
5. Password hash: pbkdf2_hmac('sha256', password, salt, 100000) → "salt:hash"

## Key Files (DO NOT BREAK THESE!)
- index.html              → handleLogin() line ~3999, loginUser() line ~2377
- dashboard.html          → getAuthHeaders() line ~96, fetch line ~1046
- backend/app/main.py     → /config route line ~371
- backend/app/services/auth_service.py → hash_password(), verify_password()

## Bugs That Were Fixed (DON'T REPEAT!)
1. Password hash mismatch → Use auth_service.hash_password() ONLY
2. Duplicate loginEmail IDs → Old modal uses oldLoginEmail now
3. JS Block 8: Quote escaping in onmouseover/onmouseout
4. JS Block 11: getPaywallHTML() needs 'async' keyword
5. handleLogin() checks data.token (NOT data.access_token)
6. loginUser() must save token + redirect to /dashboard
7. /config route MUST exist in main.py
8. Don't add catch-all route with untyped 'request' parameter

## Git Tags
- v2.0-login-working = This saved state

## To Restore If Something Breaks
1. cd /root/ml-projects/stock-prediction/deploy
2. git checkout v2.0-login-working
3. git push origin main --force
4. Deplexo → Rebuild & Redeploy
