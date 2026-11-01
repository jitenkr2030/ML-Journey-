from fastapi import APIRouter, UploadFile, File, Request, HTTPException
from fastapi.responses import FileResponse
import tempfile
import os
import csv
import logging

from app.services.upi_engine import UPIReconciliationEngine
from app.services.auth_service import get_user_by_token

logger = logging.getLogger(__name__)
router = APIRouter()
upi_engine = UPIReconciliationEngine()


async def _check_auth(request: Request):
    token = request.cookies.get("session_token", "")
    if not token:
        raise HTTPException(status_code=401, detail="Login required")
    user = await get_user_by_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Session expired")
    return user


@router.post("/api/reconcile/upi")
async def reconcile_upi(
    request: Request,
    book_file: UploadFile = File(...),
    bank_file: UploadFile = File(...)
):
    await _check_auth(request)

    # Save temp files
    book_path = _save_temp(book_file)
    bank_path = _save_temp(bank_file)

    try:
        result = upi_engine.reconcile_upi_files(book_path, bank_path)

        # Save CSV report
        report_path = _save_upi_csv_report(result)
        if report_path:
            result["report_path"] = report_path

        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"UPI reconciliation error: {e}")
        return {"success": False, "error": str(e)}
    finally:
        _cleanup(book_path, bank_path)


@router.post("/api/upi/single-match")
async def upi_single_match(request: Request):
    await _check_auth(request)
    body = await request.json()
    book_desc = body.get("book_description", "")
    bank_desc = body.get("bank_description", "")
    book_amt = float(body.get("book_amount", 0))
    bank_amt = float(body.get("bank_amount", 0))
    book_ref = body.get("book_reference", "")
    bank_ref = body.get("bank_reference", "")

    from app.services.upi_engine import (
        UPIReconciliationEngine, extract_upi_utr,
        upi_text_similarity, detect_upi_app
    )

    engine = UPIReconciliationEngine()
    features = engine._build_features(
        book_desc, bank_desc, book_amt, bank_amt,
        book_ref, bank_ref
    )
    result = engine._predict([features])[0]
    text_sim = upi_text_similarity(book_desc, bank_desc)

    return {
        "success": True,
        "result": {
            "status": result[0],
            "confidence": result[1],
            "text_similarity": round(text_sim * 100, 2),
            "upi_utr_book": extract_upi_utr(book_desc),
            "upi_utr_bank": extract_upi_utr(bank_desc),
            "upi_app": detect_upi_app(bank_desc or book_desc),
            "amount_match": abs(book_amt - bank_amt) < 0.01,
        }
    }


@router.get("/api/upi/download/{session_id}")
async def download_upi_report(session_id: str):
    report_path = f"/tmp/upi_report_{session_id}.csv"
    if os.path.exists(report_path):
        return FileResponse(report_path, filename=f"upi_reconciliation_{session_id}.csv")
    raise HTTPException(status_code=404, detail="Report not found")


def _save_temp(upload_file: UploadFile) -> str:
    suffix = os.path.splitext(upload_file.filename or "")[1] or ".csv"
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(upload_file.file.read())
    tmp.close()
    return tmp.name


def _cleanup(*paths):
    for p in paths:
        try:
            os.unlink(p)
        except:
            pass


def _save_upi_csv_report(result: dict) -> str:
    try:
        report_path = f"/tmp/upi_report_{os.getpid()}.csv"
        all_rows = result.get("matched", []) + result.get("unmatched", [])
        if not all_rows:
            return ""
        fieldnames = list(all_rows[0].keys())
        with open(report_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_rows)
        return report_path
    except Exception as e:
        logger.error(f"CSV report error: {e}")
        return ""
