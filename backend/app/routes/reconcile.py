from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import tempfile
import os
import csv
import io

from app.services.ml_engine import (
    ReconciliationEngine,
    Transaction,
)
from app.services.gst_engine import GSTReconciliationEngine

router = APIRouter()

engine = ReconciliationEngine()
gst_engine = GSTReconciliationEngine()


class SingleMatchRequest(BaseModel):
    book_description: str
    bank_description: str
    book_amount: float
    bank_amount: float
    book_reference: str = ""
    bank_reference: str = ""


class BatchMatchRequest(BaseModel):
    transactions: list


# =========================================================
# BRS ENDPOINTS
# =========================================================

@router.post("/api/reconcile/single")
async def reconcile_single(req: SingleMatchRequest):
    txn = Transaction(
        book_description=req.book_description,
        bank_description=req.bank_description,
        book_amount=req.book_amount,
        bank_amount=req.bank_amount,
        book_reference=req.book_reference,
        bank_reference=req.bank_reference,
    )
    result = engine.match_one(txn)
    return {
        "status": result.status,
        "confidence": result.confidence,
        "reason": result.reason,
    }


@router.post("/api/reconcile/batch")
async def reconcile_batch(req: BatchMatchRequest):
    transactions = []
    for t in req.transactions:
        transactions.append(
            Transaction(
                book_description=t.get("book_description", ""),
                bank_description=t.get("bank_description", ""),
                book_amount=t.get("book_amount", 0),
                bank_amount=t.get("bank_amount", 0),
                book_reference=t.get("book_reference", ""),
                bank_reference=t.get("bank_reference", ""),
            )
        )
    results = engine.match_batch(transactions)
    return {
        "total": len(results),
        "results": [
            {
                "status": r.status,
                "confidence": r.confidence,
                "reason": r.reason,
            }
            for r in results
        ],
    }


@router.post("/api/reconcile/files")
async def reconcile_files(
    book_file: UploadFile = File(...),
    bank_file: UploadFile = File(...),
):
    book_path = _save_temp(book_file)
    bank_path = _save_temp(bank_file)

    try:
        result = engine.reconcile_csv(book_path, bank_path)

        if result.get("matched") or result.get("unmatched"):
            _save_csv_report(result)

        return result
    finally:
        _cleanup(book_path, bank_path)


@router.get("/api/reconcile/download/{session_id}")
async def download_report(session_id: str):
    filepath = f"/tmp/recon_{session_id}.csv"
    if os.path.exists(filepath):
        return FileResponse(
            filepath,
            media_type="text/csv",
            filename="reconciliation_report.csv",
        )
    return {"error": "Report not found"}


# =========================================================
# GST ENDPOINTS
# =========================================================

@router.post("/api/reconcile/gst")
async def reconcile_gst(
    books_file: UploadFile = File(...),
    gstr2b_file: UploadFile = File(...),
):
    books_path = _save_temp(books_file)
    portal_path = _save_temp(gstr2b_file)

    try:
        result = gst_engine.reconcile(books_path, portal_path)

        if result.get("results"):
            _save_gst_csv_report(result)

        return result
    finally:
        _cleanup(books_path, portal_path)


@router.post("/api/gst/classify")
async def classify_invoice(invoice_text: str = Form(...)):
    result = gst_engine.classify_invoice(invoice_text)
    return result


# =========================================================
# TYPED ENDPOINT (future-proof)
# =========================================================

@router.post("/api/reconcile/{recon_type}")
async def reconcile_typed(
    recon_type: str,
    file1: UploadFile = File(...),
    file2: UploadFile = File(...),
    file3: Optional[UploadFile] = File(None),
):
    if recon_type == "brs":
        return await reconcile_files(file1, file2)
    elif recon_type == "gst":
        return await reconcile_gst(file1, file2)
    else:
        # Fall back to BRS engine for AR, AP, etc.
        return await reconcile_files(file1, file2)


# =========================================================
# HELPERS
# =========================================================

def _save_temp(upload_file: UploadFile) -> str:
    suffix = os.path.splitext(upload_file.filename)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as f:
        content = upload_file.file.read()
        f.write(content)
        return f.name


def _cleanup(*paths):
    for p in paths:
        try:
            os.unlink(p)
        except Exception:
            pass


def _save_csv_report(result: dict):
    filepath = "/tmp/recon_latest.csv"
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Book Description", "Bank Description",
            "Book Amount", "Bank Amount",
            "Status", "Confidence", "Reason"
        ])
        for row in result.get("matched", []) + result.get("unmatched", []):
            writer.writerow([
                row.get("book_description", ""),
                row.get("bank_description", ""),
                row.get("book_amount", 0),
                row.get("bank_amount", 0),
                row.get("status", ""),
                row.get("confidence", 0),
                row.get("reason", ""),
            ])


def _save_gst_csv_report(result: dict):
    filepath = "/tmp/gst_recon_latest.csv"
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Invoice Number", "GSTIN", "Vendor Name",
            "Book Taxable", "Book IGST", "Book CGST", "Book SGST", "Book Total",
            "2B Taxable", "2B IGST", "2B CGST", "2B SGST", "2B Total",
            "Status", "Category", "Confidence", "Reason"
        ])
        for row in result.get("results", []):
            writer.writerow([
                row.get("invoice_number", ""),
                row.get("gstin", ""),
                row.get("vendor_name", ""),
                row.get("book_taxable", 0),
                row.get("book_igst", 0),
                row.get("book_cgst", 0),
                row.get("book_sgst", 0),
                row.get("book_total", 0),
                row.get("portal_taxable", 0),
                row.get("portal_igst", 0),
                row.get("portal_cgst", 0),
                row.get("portal_sgst", 0),
                row.get("portal_total", 0),
                row.get("status", ""),
                row.get("category", ""),
                row.get("confidence", 0),
                row.get("reason", ""),
            ])
