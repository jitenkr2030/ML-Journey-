from fastapi import APIRouter, UploadFile, File, Form
from typing import Optional
import tempfile, os

from app.services.gst_return_engine import GSTReturnEngine

router = APIRouter()
engine = GSTReturnEngine()


@router.post("/api/gst/gstr1/prepare")
async def prepare_gstr1(sales_file: UploadFile = File(...), period: str = Form(...), client_gstin: str = Form("")):
    path = _save(sales_file)
    try:
        return engine.prepare_gstr1(path, period, client_gstin)
    finally:
        _cleanup(path)


@router.post("/api/gst/gstr2b/reconcile")
async def reconcile_gstr2b(books_file: UploadFile = File(...), gstr2b_file: UploadFile = File(...), client_gstin: str = Form("")):
    bp, pp = _save(books_file), _save(gstr2b_file)
    try:
        return engine.reconcile_gstr2b(bp, pp, client_gstin)
    finally:
        _cleanup(bp, pp)


@router.post("/api/gst/gstr3b/prepare")
async def prepare_gstr3b(sales_file: UploadFile = File(...), purchase_file: UploadFile = File(...),
                         gstr2b_file: UploadFile = File(...), period: str = Form(...), client_gstin: str = Form("")):
    sp, pp, gp = _save(sales_file), _save(purchase_file), _save(gstr2b_file)
    try:
        g1 = engine.prepare_gstr1(sp, period, client_gstin)
        g2 = engine.reconcile_gstr2b(pp, gp, client_gstin)
        return engine.prepare_gstr3b(g1, g2, period, client_gstin)
    finally:
        _cleanup(sp, pp, gp)


@router.post("/api/gst/clients/add")
async def add_client(gstin: str = Form(...), trade_name: str = Form(""), email: str = Form(""), phone: str = Form("")):
    return engine.add_client(gstin, trade_name, email, phone)


@router.get("/api/gst/clients")
async def list_clients():
    return {"clients": engine.list_clients()}


@router.get("/api/gst/clients/{gstin}/filings")
async def get_filings(gstin: str):
    return {"gstin": gstin, "filings": engine.get_client_filings(gstin)}


@router.get("/api/gst/dashboard")
async def dashboard(client_gstin: Optional[str] = None):
    return engine.get_dashboard(client_gstin)


@router.get("/api/gst/audit-trail")
async def audit_trail(client_gstin: Optional[str] = None, limit: int = 100):
    return {"audit_trail": engine.get_audit_trail(client_gstin, limit)}


def _save(upload: UploadFile) -> str:
    suffix = os.path.splitext(upload.filename)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as f:
        f.write(upload.file.read())
        return f.name


def _cleanup(*paths):
    for p in paths:
        try:
            os.unlink(p)
        except Exception:
            pass
