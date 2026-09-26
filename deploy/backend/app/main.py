from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from fastapi.responses import FileResponse
from pathlib import Path

from app.routes import reconcile
from app.routes.payments import router as payments_router
from app.routes.gst_returns import router as gst_returns_router
from app.routes.gst_filing import router as gst_filing_router

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


FRONTEND_DIR = Path("/app")

@app.get("/")
async def serve_index():
    return FileResponse(str(FRONTEND_DIR / "index.html"))

@app.get("/admin")
async def serve_admin():
    return FileResponse(str(FRONTEND_DIR / "admin.html"))

@app.get("/api/health")
async def root():
    return {
        "product": "ReconcileAI",
        "version": "3.0.0",
        "tagline": "Prepare. Reconcile. Validate. File.",
        "status": "running",
        "modules": {
            "reconciliation": {
                "brs": "/api/reconcile/files",
                "gst_recon": "/api/reconcile/gst",
            },
            "gst_returns": {
                "gstr1": "/api/gst/gstr1/prepare",
                "gstr2b": "/api/gst/gstr2b/reconcile",
                "gstr3b": "/api/gst/gstr3b/prepare",
            },
            "gst_filing": {
                "auth_init": "/api/gst/auth/init",
                "auth_verify": "/api/gst/auth/verify",
                "file_gstr1": "/api/gst/file/gstr1",
                "file_gstr3b": "/api/gst/file/gstr3b",
                "check_status": "/api/gst/filing/status/{gstin}/{arn}",
                "download_2a": "/api/gst/download/2a/{gstin}/{period}",
                "download_2b": "/api/gst/download/2b/{gstin}/{period}",
                "revoke": "/api/gst/revoke/{gstin}",
            },
            "management": {
                "clients": "/api/gst/clients",
                "dashboard": "/api/gst/dashboard",
                "audit_trail": "/api/gst/audit-trail",
                "types": "/api/types",
            },
            "payment": {
                "submit": "/api/payment/submit",
                "status": "/api/payment/status/{session_id}",
                "admin": "/api/admin/payments",
            },
            "other": {
                "single_match": "/api/reconcile/single",
                "batch_match": "/api/reconcile/batch",
                "typed_match": "/api/reconcile/{type}",
                "gst_classify": "/api/gst/classify",
                "docs": "/docs",
            },
        },
    }


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
