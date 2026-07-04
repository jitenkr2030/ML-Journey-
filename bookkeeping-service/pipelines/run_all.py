import os
import os
import sys
import time
import logging
import subprocess

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

CLIENT_NAME = os.getenv(
    "CLIENT_NAME",
    None
)

PIPELINES = [
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
    "final_report.py"
]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def run_script(script_path):
    full_path = os.path.join(
        BASE_DIR,
        script_path
    )

    if not os.path.exists(full_path):
        raise FileNotFoundError(
            f"Pipeline not found: {full_path}"
        )

    env = os.environ.copy()

    if CLIENT_NAME:
        env["CLIENT_NAME"] = CLIENT_NAME

    logging.info(
        f"Running: {script_path} for client: {CLIENT_NAME}"
    )

    start_time = time.time()

    result = subprocess.run(
        [sys.executable, full_path],
        capture_output=True,
        text=True,
        env=env
    )

    end_time = time.time()

    if result.returncode != 0:
        logging.error(
            f"Failed: {script_path}"
        )
        logging.error(result.stderr)

        raise Exception(
            f"Pipeline execution failed: {script_path}"
        )

    logging.info(
        f"Completed: {script_path} "
        f"({round(end_time - start_time, 2)} sec)"
    )

    if result.stdout:
        print(result.stdout)

def run_all():
    logging.info(
        f"Starting Full Bookkeeping Automation for {CLIENT_NAME}"
    )

    total_start = time.time()

    for pipeline in PIPELINES:
        run_script(pipeline)

    total_end = time.time()

    logging.info(
        "All Pipelines Completed Successfully"
    )

    logging.info(
        f"Total Execution Time: "
        f"{round(total_end - total_start, 2)} sec"
    )

if __name__ == "__main__":
    run_all()
