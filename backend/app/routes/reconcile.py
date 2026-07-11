# backend/app/routes/reconcile.py
from fastapi import APIRouter, UploadFile, File
from app.services.ml_engine import ReconciliationEngine, Transaction

router = APIRouter()
engine = ReconciliationEngine()


@router.post("/api/reconcile/single")
async def reconcile_single(transaction: dict):
    """Match a single book entry against a bank entry"""
    txn = Transaction(
        book_description=transaction["book_description"],
        bank_description=transaction["bank_description"],
        book_amount=float(transaction["book_amount"]),
        bank_amount=float(transaction["bank_amount"]),
        book_reference=transaction["book_reference"],
        bank_reference=transaction["bank_reference"],
    )
    result = engine.match_one(txn)
    return engine._to_dict(result)


@router.post("/api/reconcile/batch")
async def reconcile_batch(transactions: list[dict]):
    """Match multiple transaction pairs at once"""
    txns = [
        Transaction(
            book_description=t["book_description"],
            bank_description=t["bank_description"],
            book_amount=float(t["book_amount"]),
            bank_amount=float(t["bank_amount"]),
            book_reference=t["book_reference"],
            bank_reference=t["bank_reference"],
        )
        for t in transactions
    ]
    results = engine.match_batch(txns)
    return [engine._to_dict(r) for r in results]


@router.post("/api/reconcile/files")
async def reconcile_files(
    book_file: UploadFile = File(...),
    bank_file: UploadFile = File(...),
):
    """Upload two CSV files and get full reconciliation"""
    import tempfile
    import os

    # Save uploads temporarily
    book_path = tempfile.mktemp(suffix=".csv")
    bank_path = tempfile.mktemp(suffix=".csv")

    with open(book_path, "wb") as f:
        f.write(await book_file.read())
    with open(bank_path, "wb") as f:
        f.write(await bank_file.read())

    results = engine.reconcile_csv(book_path, bank_path)

    os.unlink(book_path)
    os.unlink(bank_path)

    return results
