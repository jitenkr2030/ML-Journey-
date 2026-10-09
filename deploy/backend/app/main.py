from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from dotenv import load_dotenv
load_dotenv()
from fastapi.responses import FileResponse
from pathlib import Path

from app.routes import reconcile
from app.routes.payments import router as payments_router
from app.routes.gst_returns import router as gst_returns_router
from app.routes.gst_filing import router as gst_filing_router
from app.routes.bookkeeping import router as bookkeeping_router
from app.routes.auth import router as auth_router
from app.routes.dashboard import router as dashboard_router
from app.routes.admin import router as admin_router

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

@app.on_event("startup")
async def startup():
    from app.services.auth_service import create_admin_user, get_pool
    await get_pool()
    await create_admin_user()


@app.get("/")
async def root():
    return FileResponse(str(Path(__file__).resolve().parent.parent.parent / "index.html"))

@app.get("/admin")
async def serve_admin():
    return FileResponse(str(Path(__file__).resolve().parent.parent.parent / "admin.html"))

@app.get("/dashboard")
async def serve_dashboard():
    return FileResponse(str(Path(__file__).resolve().parent.parent.parent / "dashboard.html"))

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
