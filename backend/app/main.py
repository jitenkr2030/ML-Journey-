import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging
from dotenv import load_dotenv
load_dotenv()
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from pathlib import Path

from app.routes import reconcile
from app.routes.payments import router as payments_router
from app.routes.gst_returns import router as gst_returns_router
from app.routes.gst_filing import router as gst_filing_router
from app.routes.bookkeeping import router as bookkeeping_router
from app.routes.auth import router as auth_router
from app.routes.dashboard import router as dashboard_router
from app.routes.admin import router as admin_router
from app.routes.upi import router as upi_router
from app.routes.history import router as history_router
from app.routes.clients import router as clients_router
from app.routes.usage import router as usage_router
from app.routes.service_inquiries import router as inquiries_router

logger = logging.getLogger(__name__)

app = FastAPI(
    title="ReconcileAI — GST & Bank Reconciliation Platform",
    description="AI-powered reconciliation and GST compliance for Indian businesses",
    version="3.0.0",
)

# ===== Security Middleware: Block Scanner Bots =====
import time as _time
from collections import defaultdict as _ddict

_BLOCKED_PATHS = [
    '.env', '.git', 'wp-admin', 'wp-login', 'wp-includes', 'wp-content',
    'phpinfo', 'info.php', 'php.php', 'p.php', 'i.php', 'debug.php',
    'test.php', 'pinfo.php', 'server-info', 'server-status',
    'service-account.json', 'credentials.json', 'sa.json',
    'gcp-key.json', 'google-credentials.json', 'firebase-adminsdk',
    'application_default_credentials', 'keyfile.json',
    'cache.php', '.DS_Store', 'web.config', 'elmah.axd',
    'xmlrpc.php', 'wlwmanifest.xml', 'install.php',
    '.htaccess', '.htpasswd', 'passwd', 'shadow',
    'etc/passwd', 'proc/self', 'boot.ini', 'win.ini',
    'config.json', 'settings.py', 'database.yml',
    'phpmyadmin', 'adminer', 'pma', 'myadmin',
    '.svn', '.hg', '.bzr', 'CVS',
    'actuator', 'jmx-console', 'manager/html',
    'shell', 'cmd', 'eval', 'exec',
]

_RATE_LIMIT = {}  # ip -> [timestamps]
_RATE_LIMIT_WINDOW = 60  # seconds
_RATE_LIMIT_MAX = 120  # requests per window per IP


import os as _os_serve

def _find_html_root():
    """Find where HTML files are located."""
    _candidates = [
        _os_serve.path.join(_os_serve.path.dirname(_os_serve.path.abspath(__file__)), "static"),
        _os_serve.path.dirname(_os_serve.path.abspath(__file__)),
        _os_serve.path.dirname(_os_serve.path.dirname(_os_serve.path.abspath(__file__))),
        _os_serve.path.join(_os_serve.path.dirname(_os_serve.path.dirname(_os_serve.path.abspath(__file__))), "deploy"),
        "/app",
    ]
    for _c in _candidates:
        if _os_serve.path.exists(_os_serve.path.join(_c, "index.html")):
            return _c
    return _os_serve.path.dirname(_os_serve.path.dirname(_os_serve.path.abspath(__file__)))


# ===== APP_ROOT: Where HTML files live =====

# ===== APP_ROOT: Where HTML files are located =====
APP_ROOT = r"/root/ml-projects/stock-prediction"
# Auto-detect for Docker deployment:
for _p in ["/app", r"/root/ml-projects/stock-prediction", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "deploy"), os.path.dirname(os.path.dirname(os.path.abspath(__file__))), os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))]:
    if os.path.exists(os.path.join(_p, "index.html")) and os.path.exists(os.path.join(_p, "tools.html")):
        APP_ROOT = _p
        break


@app.middleware("http")
async def security_middleware(request, call_next):
    path = request.url.path.lower()
    client_ip = request.client.host if request.client else "unknown"

    # ALWAYS allow search engine bots (check User-Agent)
    user_agent = request.headers.get("user-agent", "").lower()
    _GOOD_BOTS = ["googlebot", "bingbot", "slurp", "duckduckbot",
                  "baiduspider", "yandexbot", "facebookexternalhit",
                  "twitterbot", "linkedinbot", "whatsapp", "telegrambot",
                  "applebot", "petalbot", "sogou"]

    is_good_bot = any(bot in user_agent for bot in _GOOD_BOTS)

    # Block scanner paths (but NOT for search engine bots)
    if not is_good_bot:
        for blocked in _BLOCKED_PATHS:
            if blocked in path:
                return JSONResponse(
                    status_code=403,
                    content={"error": "Forbidden"}
                )

    # Rate limiting per IP (skip for search engine bots)
    if not is_good_bot:
        now = _time.time()
        if client_ip not in _RATE_LIMIT:
            _RATE_LIMIT[client_ip] = []
        _RATE_LIMIT[client_ip] = [t for t in _RATE_LIMIT[client_ip] if now - t < _RATE_LIMIT_WINDOW]
        if len(_RATE_LIMIT[client_ip]) >= _RATE_LIMIT_MAX:
            return JSONResponse(status_code=429, content={"error": "Too many requests"})
        _RATE_LIMIT[client_ip].append(now)

    # Rate limiting per IP
    now = _time.time()
    if client_ip not in _RATE_LIMIT:
        _RATE_LIMIT[client_ip] = []

    # Clean old timestamps
    _RATE_LIMIT[client_ip] = [t for t in _RATE_LIMIT[client_ip] if now - t < _RATE_LIMIT_WINDOW]

    if len(_RATE_LIMIT[client_ip]) >= _RATE_LIMIT_MAX:
        return JSONResponse(
            status_code=429,
            content={"error": "Too many requests"}
        )

    _RATE_LIMIT[client_ip].append(now)

    # Periodic cleanup of old IPs (every 1000 requests)
    if len(_RATE_LIMIT) > 1000:
        for ip in list(_RATE_LIMIT.keys()):
            if not any(now - t < _RATE_LIMIT_WINDOW for t in _RATE_LIMIT[ip]):
                del _RATE_LIMIT[ip]

    response = await call_next(request)
    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(reconcile.router)
app.include_router(payments_router)
app.include_router(gst_returns_router)
app.include_router(gst_filing_router)
app.include_router(bookkeeping_router)
app.include_router(auth_router)
app.include_router(dashboard_router)
app.include_router(admin_router)
app.include_router(upi_router)
app.include_router(history_router)
app.include_router(clients_router)
app.include_router(usage_router)
app.include_router(inquiries_router)

@app.on_event("startup")
async def startup():
    try:
        from app.services.auth_service import create_admin_user, get_pool
        await get_pool()
        await create_admin_user()
    except Exception as e:
        print(f"WARNING: Startup error (non-fatal): {e}")
        import traceback
        traceback.print_exc()
        print("App started despite errors. Some features may be limited.")
        print("If DB is down: Power ON at Aiven dashboard!")


# ===== Festival Auto-Theme System =====

# ===== Googlebot bypass (SAFE: never touches API routes) =====
@app.middleware("http")
async def _googlebot_auth_bypass(request, call_next):
    """Allow search engine bots to crawl public pages. NEVER touches /api/ routes."""
    path = request.url.path

    # CRITICAL: Do NOT touch API routes at all!
    if path.startswith("/api/"):
        return await call_next(request)

    # Only affect public page routes
    ua = request.headers.get("user-agent", "")
    is_bot = any(bot in ua for bot in ["Googlebot", "Bingbot", "Slurp", "DuckDuckBot"])

    if is_bot:
        try:
            response = await call_next(request)
            response.headers["X-Robots-Tag"] = "index, follow"
            return response
        except Exception:
            return HTMLResponse("<html><body>OK</body></html>", status_code=200)

    return await call_next(request)

@app.middleware("http")
async def _googlebot_auth_bypass(request: Request, call_next):
    """Allow Googlebot to access pages without auth."""
    ua = request.headers.get("user-agent", "")
    path = request.url.path

    # Only affect public page routes (not API)
    is_bot = any(bot in ua for bot in ["Googlebot", "Bingbot", "Slurp", "DuckDuckBot", "facebookexternalhit", "Twitterbot", "LinkedInBot"])
    is_page = not path.startswith("/api/") and not path.startswith("/admin")

    if is_bot and is_page:
        # Skip auth for bots on public pages
        request.state.skip_auth = True

    response = await call_next(request)

    # Add headers Google likes
    if is_bot and is_page:
        response.headers["X-Robots-Tag"] = "index, follow"

    return response


# ===== Error handler (SAFE: never catches API errors) =====
@app.middleware("http")
async def _no_5xx_for_pages(request, call_next):
    """Catch errors on page routes only. API routes work normally."""
    path = request.url.path

    # CRITICAL: Let API routes work normally!
    if path.startswith("/api/"):
        return await call_next(request)

    try:
        response = await call_next(request)
        return response
    except Exception:
        # For pages, serve index.html instead of 500
        try:
            idx = os.path.join(APP_ROOT, "index.html")
            if os.path.exists(idx):
                return FileResponse(idx, media_type="text/html", status_code=200)
        except Exception:
            pass
        return HTMLResponse("<html><body><h1>ReconcileAI</h1></body></html>", status_code=200)

@app.middleware("http")
async def _no_5xx_for_pages(request: Request, call_next):
    """Catch all errors and return 200 for page routes."""
    path = request.url.path
    is_page = not path.startswith("/api/") and not path.startswith("/admin")

    try:
        response = await call_next(request)
        return response
    except Exception as e:
        if is_page:
            # For pages, serve index.html instead of 500 error
            import os as _os
            try:
                idx = _os.path.join(APP_ROOT, "index.html")
                if _os.path.exists(idx):
                    return FileResponse(idx, media_type="text/html", status_code=200)
            except:
                pass
            return HTMLResponse("<html><body><h1>ReconcileAI</h1></body></html>", status_code=200)
        # For API, return proper error
        return JSONResponse(status_code=500, content={"error": str(e)})

    return await call_next(request)



@app.get("/compare")
async def compare_page():
    return _serve_page("compare.html")

@app.get("/best-reconciliation-software-india")
async def best_recon_page():
    return _serve_page("best-reconciliation-software-india.html")

@app.get("/faq")
async def faq_page():
    return _serve_page("faq.html")

@app.get("/festival-themes.css")
def _festival_css():
    return FileResponse(os.path.join(APP_ROOT, "festival-themes.css"), media_type="text/css")

@app.get("/festival-config.js")
def _festival_config():
    return FileResponse(os.path.join(APP_ROOT, "festival-config.js"), media_type="application/javascript")

@app.get("/festival-engine.js")
def _festival_engine():
    return FileResponse(os.path.join(APP_ROOT, "festival-engine.js"), media_type="application/javascript")

@app.get("/")
async def root():
    return FileResponse(str(Path(__file__).resolve().parent.parent.parent / "index.html"))

@app.get("/admin.html")
async def admin_html():
    return FileResponse(str(Path(__file__).resolve().parent.parent.parent / "admin.html"))

@app.get("/dashboard.html")
async def dashboard_html():
    return FileResponse(str(Path(__file__).resolve().parent.parent.parent / "dashboard.html"))

@app.get("/admin")
async def serve_admin():
    return FileResponse(str(Path(__file__).resolve().parent.parent.parent / "admin.html"))

@app.get("/dashboard")
async def serve_dashboard():
    return FileResponse(str(Path(__file__).resolve().parent.parent.parent / "dashboard.html"))


# ==================== FREE TOOLS ====================
def _serve_page(*parts):
    """Serve HTML page from APP_ROOT."""
    import os as _osp
    from fastapi.responses import FileResponse, JSONResponse

    # Build the file path
    file_path = _osp.path.join(APP_ROOT, *parts)

    # If directory, look for index.html inside
    if _osp.path.isdir(file_path):
        file_path = _osp.path.join(file_path, "index.html")

    # If no .html extension and file doesn't exist, try adding .html
    if not file_path.endswith(".html") and not _osp.path.isfile(file_path):
        file_path += ".html"

    # Serve the file
    if _osp.path.isfile(file_path):
        return FileResponse(file_path, media_type="text/html")

    # File not found — return 404 (NOT index.html!)
    return JSONResponse(
        status_code=404,
        content={"error": "Page not found: " + "/".join(parts)}
    )

@app.get("/favicon.ico")
async def favicon():
    import os as _f_os
    from fastapi.responses import FileResponse as _f_FR
    _f_base = _f_os.path.join(_f_os.path.dirname(_f_os.path.dirname(_f_os.path.dirname(_f_os.path.abspath(__file__)))), "favicon.svg")
    return _f_FR(_f_base, media_type="image/svg+xml")

@app.get("/favicon.svg")
async def favicon_svg():
    import os as _f_os
    from fastapi.responses import FileResponse as _f_FR
    _f_base = _f_os.path.join(_f_os.path.dirname(_f_os.path.dirname(_f_os.path.dirname(_f_os.path.abspath(__file__)))), "favicon.svg")
    return _f_FR(_f_base, media_type="image/svg+xml")

@app.get("/tools")
async def tools_index():
    return _serve_page("tools.html")

@app.get("/tools/gst-calculator")
async def gst_calculator():
    return _serve_page("free-tools", "gst-calculator", "index.html")

@app.get("/tools/tds-calculator")
async def tds_calculator():
    return _serve_page("free-tools", "tds-calculator", "index.html")

@app.get("/tools/income-tax-calculator")
async def income_tax_calculator():
    return _serve_page("free-tools", "income-tax-calculator", "index.html")


@app.get("/tools/hra-calculator")
async def hra_calculator():
    return _serve_page("free-tools", "hra-calculator", "index.html")


@app.get("/tools/capital-gains-calculator")
async def capital_gains_calc():
    return _serve_page("free-tools", "capital-gains-calculator", "index.html")

@app.get("/tools/emi-calculator")
async def emi_calculator():
    return _serve_page("free-tools", "emi-calculator", "index.html")

@app.get("/tools/fd-calculator")
async def fd_calculator():
    return _serve_page("free-tools", "fd-calculator", "index.html")


@app.get("/tools/sip-calculator")
async def sip_calculator():
    return _serve_page("free-tools", "sip-calculator", "index.html")

@app.get("/tools/advance-tax-calculator")
async def advance_tax_calculator():
    return _serve_page("free-tools", "advance-tax-calculator", "index.html")

@app.get("/tools/depreciation-calculator")
async def depreciation_calculator():
    return _serve_page("free-tools", "depreciation-calculator", "index.html")


@app.get("/tools/gratuity-calculator")
async def gratuity_calculator():
    return _serve_page("free-tools", "gratuity-calculator", "index.html")

@app.get("/tools/pf-calculator")
async def pf_calculator():
    return _serve_page("free-tools", "pf-calculator", "index.html")

@app.get("/tools/markup-calculator")
async def markup_calculator():
    return _serve_page("free-tools", "markup-calculator", "index.html")


@app.get("/tools/break-even-calculator")
async def break_even_calculator():
    return _serve_page("free-tools", "break-even-calculator", "index.html")

@app.get("/tools/roi-calculator")
async def roi_calculator():
    return _serve_page("free-tools", "roi-calculator", "index.html")

@app.get("/tools/interest-calculator")
async def interest_calculator():
    return _serve_page("free-tools", "interest-calculator", "index.html")

@app.get("/tools/currency-converter")
async def currency_converter():
    return _serve_page("free-tools", "currency-converter", "index.html")


# ===== Global Exception Handler: Never Crash =====
import traceback as _tb
import logging as _logging

_crash_logger = _logging.getLogger("crash_handler")
_crash_logger.setLevel(_logging.ERROR)

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    _crash_logger.error(f"UNHANDLED ERROR on {request.url.path}: {exc}")
    _crash_logger.error(_tb.format_exc())
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if "DEBUG" in str(exc) else "Something went wrong. Please try again.",
            "path": str(request.url.path)
        }
    )


# ===== Extensions Store =====
@app.get("/extensions")
async def extensions_page():
    try:
        return _serve_page("extensions", "index.html")
    except Exception as e:
        return JSONResponse(status_code=404, content={"error": "Page not found"})

@app.get("/blog")
async def blog_index():
    return _serve_page("blog", "index.html")

@app.get("/blog/{slug}")
async def blog_post(slug: str):
    try:
        return _serve_page("blog", f"{slug}.html")
    except Exception as e:
        _crash_logger.error(f"Blog post error: {slug} - {e}")
        return JSONResponse(status_code=404, content={"error": "Post not found"})

@app.get("/sitemap.xml")
async def sitemap():
    import os as _os
    from fastapi.responses import FileResponse as _FR
    _base = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))), "sitemap.xml")
    return _FR(_base, media_type="application/xml")

@app.get("/robots.txt")
async def robots():
    import os as _os
    from fastapi.responses import FileResponse as _FR
    _base = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))), "robots.txt")
    return _FR(_base, media_type="text/plain")


# ===== Excel Template Downloads =====
import os as _os
from fastapi.responses import FileResponse as _FileResp

_TPL_BASE = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))), "templates")

@app.get("/templates")
async def templates_index():
    return _serve_page("templates", "index.html")

@app.get("/templates/download/{slug}")
async def download_template(slug: str):
    try:
        fpath = _os.path.join(_TPL_BASE, f"{slug}.xlsx")
        if not _os.path.exists(fpath):
            return JSONResponse(status_code=404, content={"error": "Template not found"})
        return _FileResp(
            fpath,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=f"{slug}.xlsx",
            headers={"Content-Disposition": f'attachment; filename="{slug}.xlsx"'}
        )
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/templates/{slug}")
async def template_page(slug: str):
    return _serve_page("templates", slug, "index.html")

@app.get("/api/types")
async def list_types():
    return {
        "types": [
            {
                "id": "brs",
                "name": "Bank Reconciliation (BRS)",
                "description": "Match bank statement against bank ledger",
                "icon": "🏦",
                "category": "reconciliation",
                "price": 299,
                "enabled": True,
                "files": [
                    {"role": "book_file", "label": "Bank Ledger (Tally)", "required": True},
                    {"role": "bank_file", "label": "Bank Statement", "required": True},
                ],
                "statuses": ["Matched", "Unmatched", "Unmatched Bank", "Skipped"],
            },
            {
                "id": "gst",
                "name": "GST Reconciliation",
                "description": "Match books against GSTR-2B with auto-classification",
                "icon": "📋",
                "category": "reconciliation",
                "price": 299,
                "enabled": True,
                "files": [
                    {"role": "books_file", "label": "Purchase Register / Books", "required": True},
                    {"role": "gstr2b_file", "label": "GSTR-2B (from GST portal)", "required": True},
                ],
                "statuses": ["Matched", "Invoice Mismatch", "Amount Mismatch",
                             "GSTIN Mismatch", "Missing in GSTR-2B", "Missing in Books"],
            },
            {
                "id": "gstr1",
                "name": "GSTR-1 Preparation & Filing",
                "description": "Prepare and file GSTR-1 from sales data",
                "icon": "📤",
                "category": "gst_returns",
                "price": 299,
                "enabled": True,
                "files": [
                    {"role": "sales_file", "label": "Sales Register / Invoices", "required": True},
                ],
                "statuses": ["B2B", "B2CL", "B2CS", "Export", "Credit Note", "Debit Note"],
            },
            {
                "id": "gstr2b",
                "name": "GSTR-2B Reconciliation",
                "description": "Reconcile GSTR-2B with purchase register for ITC",
                "icon": "📥",
                "category": "gst_returns",
                "price": 299,
                "enabled": True,
                "files": [
                    {"role": "books_file", "label": "Purchase Register / Books", "required": True},
                    {"role": "gstr2b_file", "label": "GSTR-2B (from GST portal)", "required": True},
                ],
                "statuses": ["Matched", "Mismatched", "Missing in 2B", "Missing in Books"],
            },
            {
                "id": "gstr3b",
                "name": "GSTR-3B Preparation & Filing",
                "description": "Prepare and file GSTR-3B with auto-computed tax liability",
                "icon": "🧮",
                "category": "gst_returns",
                "price": 299,
                "enabled": True,
                "files": [
                    {"role": "sales_file", "label": "Sales Register", "required": True},
                    {"role": "purchase_file", "label": "Purchase Register", "required": True},
                    {"role": "gstr2b_file", "label": "GSTR-2B", "required": True},
                ],
                "statuses": ["Computed", "Tax Payable", "ITC Available", "ITC Blocked"],
            },
            {
                "id": "tds",
                "name": "TDS Reconciliation",
                "description": "Match books against Form 26AS / TRACES",
                "icon": "📄",
                "category": "reconciliation",
                "price": 299,
                "enabled": False,
                "coming_soon": True,
                "files": [],
                "statuses": [],
            },
            {
                "id": "ar",
                "name": "Customer (AR) Reconciliation",
                "description": "Match customer ledger against customer statements",
                "icon": "👥",
                "category": "reconciliation",
                "price": 299,
                "enabled": False,
                "coming_soon": True,
                "files": [],
                "statuses": [],
            },
            {
                "id": "ap",
                "name": "Vendor (AP) Reconciliation",
                "description": "Match vendor ledger against vendor statements",
                "icon": "🏭",
                "category": "reconciliation",
                "price": 299,
                "enabled": False,
                "coming_soon": True,
                "files": [],
                "statuses": [],
            },
            {
                "id": "ecomm",
                "name": "E-commerce Settlement",
                "description": "Match Amazon/Flipkart settlement against sales ledger",
                "icon": "🛒",
                "category": "reconciliation",
                "price": 299,
                "enabled": False,
                "coming_soon": True,
                "files": [],
                "statuses": [],
            },
        ]
    }

# ===== SEO: Safe error handler =====
from starlette.exceptions import HTTPException as _StarletteHTTPException

@app.exception_handler(_StarletteHTTPException)
async def _http_error_handler(request: Request, exc: _StarletteHTTPException):
    """Handle 404s — only serve index.html for truly unknown paths."""
    _path = request.url.path
    # Never intercept these known routes:
    _skip = ['/api/', '/data/', '/static', '/favicon', '/sitemap', '/robots',
             '/tools', '/blog', '/templates', '/extensions', '/free-tools',
             '/dashboard', '/admin']
    for _s in _skip:
        if _path.startswith(_s):
            return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    # For truly unknown paths, serve index.html (SPA behavior)
    try:
        _idx = os.path.join(APP_ROOT, "index.html")
        if os.path.exists(_idx):
            return FileResponse(_idx, media_type="text/html", status_code=200)
    except:
        pass
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

@app.exception_handler(Exception)
async def _global_error_handler(request: Request, exc: Exception):
    """Log and return 500."""
    import logging
    logging.error(f"Error on {request.url.path}: {exc}")
    return JSONResponse(status_code=500, content={"error": str(exc)})


# ===== SEO: Error handlers (prevent 5xx for Google) =====
from starlette.exceptions import HTTPException as _StarletteHTTPException

@app.exception_handler(_StarletteHTTPException)
async def _http_error_handler(request: Request, exc: _StarletteHTTPException):
    """Handle 404/5xx gracefully — serve index.html for SEO."""
    import os as _os
    if exc.status_code == 404:
        _idx = _os.path.join(APP_ROOT, "index.html")
        if _os.path.exists(_idx):
            return FileResponse(_idx, media_type="text/html", status_code=200)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.exception_handler(Exception)
async def _global_error_handler(request: Request, exc: Exception):
    """Catch all errors — never return 5xx to Google."""
    import os as _os
    _idx = _os.path.join(APP_ROOT, "index.html")
    if _os.path.exists(_idx):
        return FileResponse(_idx, media_type="text/html", status_code=200)
    return JSONResponse(status_code=200, content={"status": "ok"})
