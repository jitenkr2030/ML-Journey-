from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from dotenv import load_dotenv
load_dotenv()
from fastapi.responses import FileResponse, HTMLResponse
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
    from app.services.auth_service import create_admin_user, get_pool
    await get_pool()
    await create_admin_user()


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
    """Safely serve a static page with fallback paths."""
    base = Path(__file__).resolve().parent.parent.parent
    for root in [base, base.parent, Path.cwd() / "deploy"]:
        p = root.joinpath(*parts)
        if p.exists():
            return FileResponse(str(p))
    return HTMLResponse(f"<h1>404 - Page not found</h1><p>Looking for: {'/'.join(parts)}</p>", status_code=404)

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


@app.get("/blog")
async def blog_index():
    return _serve_page("blog", "index.html")

@app.get("/blog/{slug}")
async def blog_post(slug: str):
    return _serve_page("blog", f"{slug}.html")

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
    fpath = _os.path.join(_TPL_BASE, f"{slug}.xlsx")
    if not _os.path.exists(fpath):
        return {"error": "Template not found"}
    return _FileResp(
        fpath,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=f"{slug}.xlsx",
        headers={"Content-Disposition": f'attachment; filename="{slug}.xlsx"'}
    )

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
                "price": 499,
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
                "price": 499,
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
                "price": 499,
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
                "price": 499,
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
                "price": 499,
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
                "price": 499,
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
                "price": 499,
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
                "price": 499,
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
                "price": 499,
                "enabled": False,
                "coming_soon": True,
                "files": [],
                "statuses": [],
            },
        ]
    }
