# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import reconcile
from app.routes.payments import router as payments_router

app = FastAPI(
    title="Bank Reconciliation AI",
    description="AI-powered bank statement reconciliation for Indian businesses",
    version="1.0.0",
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


@app.get("/")
async def root():
    return {
        "product": "Bank Reconciliation AI",
        "status": "running",
        "endpoints": {
            "single_match": "/api/reconcile/single",
            "batch_match": "/api/reconcile/batch",
            "file_upload": "/api/reconcile/files",
            "payment_submit": "/api/payment/submit",
            "payment_status": "/api/payment/status/{session_id}",
            "admin_payments": "/api/admin/payments",
            "admin_verify": "/api/admin/verify/{id}",
            "admin_reject": "/api/admin/reject/{id}",
            "docs": "/docs",
        },
    }
