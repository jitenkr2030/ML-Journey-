import os
import sys
import subprocess
import shutil
import zipfile
import logging
import uuid
import time
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse

router = APIRouter(prefix="/api/bookkeeping", tags=["bookkeeping"])

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR = Path("/root/ml-projects/stock-prediction/bookkeeping-service")

JOBS = {}

OUTPUT_FILES = [
    "accounting/accounting_output.csv",
    "accounting/manual_review.csv",
    "accounting/journal_entries.csv",
    "accounting/trial_balance.csv",
    "accounting/profit_and_loss.csv",
    "accounting/balance_sheet.csv",
    "accounting/cash_flow.csv",
    "financial/working_notes.csv",
    "financial/annexure_report.csv",
    "financial/schedules.csv",
    "financial/depreciation_chart.csv",
    "financial/audit_trail.csv",
    "financial/compliance_checklist.csv",
    "financial/tax_computation.csv",
    "financial/risk_analysis.csv",
    "financial/closing_checklist.csv",
    "financial/client_advisory.csv",
    "financial/year_end_finalization.csv",
    "financial/financial_ratios.csv",
    "ledgers/ledgers.csv",
    "reports/compliance_summary.csv",
    "reports/final_client_report.csv",
    "reports/management_summary.csv",
]

PIPELINE_NAMES = [
    "SBI Bank Cleaner",
    "Tally Daybook Cleaner",
    "Accounting Pipeline",
    "Bank Pipeline",
    "GST Pipeline",
    "TDS Pipeline",
    "Ledger Pipeline",
    "Depreciation Pipeline",
    "Working Notes Pipeline",
    "Annexure Pipeline",
    "Schedule Pipeline",
    "Audit Trail Pipeline",
    "Financial Statement Pipeline",
    "Compliance Checklist Pipeline",
    "Tax Computation Pipeline",
    "Risk Analysis Pipeline",
    "Closing Checklist Pipeline",
    "Client Advisory Pipeline",
    "Year-End Finalization Pipeline",
    "Ratio Analysis",
    "Final Report",
]


@router.post("/upload")
async def upload_files(
    bank_statement: UploadFile = File(...),
    daybook: UploadFile = File(...),
    transactions: UploadFile = File(None),
):
    job_id = str(uuid.uuid4())[:8]
    job_dir = BASE_DIR / "data" / "clients" / job_id
    raw_dir = job_dir / "input"
    out_dir = job_dir / "output"
    rep_dir = job_dir / "reports"
    proc_dir = job_dir / "processed"

    for d in [raw_dir, out_dir, rep_dir, proc_dir]:
        d.mkdir(parents=True, exist_ok=True)

    for sub in ["accounting", "banking", "gst", "tds", "financial", "ledgers"]:
        (out_dir / sub).mkdir(parents=True, exist_ok=True)

    with open(raw_dir / "bank_statement.csv", "wb") as f:
        f.write(await bank_statement.read())

    with open(raw_dir / "daybook.csv", "wb") as f:
        f.write(await daybook.read())

    if transactions:
        with open(raw_dir / "transactions.csv", "wb") as f:
            f.write(await transactions.read())

    JOBS[job_id] = {
        "status": "uploaded",
        "progress": 0,
        "total_pipelines": len(PIPELINE_NAMES),
        "completed_pipelines": [],
        "current_pipeline": None,
        "start_time": None,
        "end_time": None,
        "output_files": [],
        "error": None,
    }

    return {"job_id": job_id, "status": "uploaded", "message": "Files uploaded successfully"}


@router.post("/run/{job_id}")
async def run_bookkeeping(job_id: str):
    if job_id not in JOBS:
        raise HTTPException(status_code=404, detail="Job not found")

    job = JOBS[job_id]
    if job["status"] == "running":
        raise HTTPException(status_code=400, detail="Job already running")

    job["status"] = "running"
    job["start_time"] = time.time()
    job["completed_pipelines"] = []
    job["error"] = None

    client_path = BASE_DIR / "data" / "clients" / job_id

    env = os.environ.copy()
    env["CLIENT_NAME"] = ""
    env["BK_RAW_DIR"] = str(client_path / "input")
    env["BK_OUTPUT_DIR"] = str(client_path / "output")
    env["BK_REPORTS_DIR"] = str(client_path / "reports")
    env["BK_PROCESSED_DIR"] = str(client_path / "processed")

    pipelines = [
        "../cleaners/sbi_bank_cleaner.py",
        "../cleaners/tally_daybook_cleaner.py",
        "accounting_pipeline.py",
        "bank_pipeline.py",
        "gst_pipeline.py",
        "tds_pipeline.py",
        "ledger_pipeline.py",
        "depreciation_pipeline.py",
        "working_notes_pipeline.py",
        "annexure_pipeline.py",
        "schedule_pipeline.py",
        "audit_trail_pipeline.py",
        "financial_statement_pipeline.py",
        "compliance_checklist_pipeline.py",
        "tax_computation_pipeline.py",
        "risk_analysis_pipeline.py",
        "closing_checklist_pipeline.py",
        "client_advisory_pipeline.py",
        "year_end_finalization_pipeline.py",
        "ratio_analysis.py",
        "final_report.py",
    ]

    pipeline_dir = BASE_DIR / "pipelines"

    try:
        for i, pipeline in enumerate(pipelines):
            job["current_pipeline"] = PIPELINE_NAMES[i]
            job["progress"] = i

            script_path = pipeline_dir / pipeline

            if not script_path.exists():
                logger.warning(f"Pipeline not found: {script_path}")
                job["completed_pipelines"].append({"name": PIPELINE_NAMES[i], "status": "skipped"})
                continue

            result = subprocess.run(
                [sys.executable, str(script_path)],
                capture_output=True,
                text=True,
                env=env,
                cwd=str(pipeline_dir),
                timeout=120,
            )

            if result.returncode != 0:
                logger.error(f"Pipeline failed: {pipeline}: {result.stderr[:200]}")
                job["completed_pipelines"].append({"name": PIPELINE_NAMES[i], "status": "failed"})
            else:
                job["completed_pipelines"].append({"name": PIPELINE_NAMES[i], "status": "completed"})

        job["status"] = "completed"
        job["progress"] = len(PIPELINE_NAMES)
        job["end_time"] = time.time()

        output_dir = client_path / "output"
        report_dir = client_path / "reports"

        files = []
        if output_dir.exists():
            for f in output_dir.rglob("*.csv"):
                files.append(str(f.relative_to(client_path)))
        if report_dir.exists():
            for f in report_dir.rglob("*.csv"):
                files.append(str(f.relative_to(client_path)))

        job["output_files"] = files

    except Exception as e:
        job["status"] = "failed"
        job["error"] = str(e)
        logger.error(f"Bookkeeping failed: {e}")

    return {
        "job_id": job_id,
        "status": job["status"],
        "progress": job["progress"],
        "completed_pipelines": job["completed_pipelines"],
        "output_files": job["output_files"],
        "error": job["error"],
    }


@router.get("/status/{job_id}")
async def get_status(job_id: str):
    if job_id not in JOBS:
        raise HTTPException(status_code=404, detail="Job not found")

    job = JOBS[job_id]
    return {
        "job_id": job_id,
        "status": job["status"],
        "progress": job["progress"],
        "total_pipelines": job["total_pipelines"],
        "current_pipeline": job["current_pipeline"],
        "completed_pipelines": job["completed_pipelines"],
        "output_files": job["output_files"],
        "error": job["error"],
        "start_time": job["start_time"],
        "end_time": job["end_time"],
    }


@router.get("/download/{job_id}")
async def download_all(job_id: str):
    if job_id not in JOBS:
        raise HTTPException(status_code=404, detail="Job not found")

    client_path = BASE_DIR / "data" / "clients" / job_id
    zip_path = client_path / f"bookkeeping_reports_{job_id}.zip"

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in client_path.rglob("*.csv"):
            if "input" not in str(f):
                zf.write(f, f.relative_to(client_path))

    return FileResponse(
        str(zip_path),
        media_type="application/zip",
        filename=f"bookkeeping_reports_{job_id}.zip",
    )


@router.get("/download/{job_id}/{filename}")
async def download_file(job_id: str, filename: str):
    if job_id not in JOBS:
        raise HTTPException(status_code=404, detail="Job not found")

    client_path = BASE_DIR / "data" / "clients" / job_id

    for f in client_path.rglob(filename):
        return FileResponse(str(f))

    raise HTTPException(status_code=404, detail="File not found")
