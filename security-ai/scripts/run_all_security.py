import os
import sys
import time
import logging
import subprocess
from pathlib import Path

# ============================================================
# BASE CONFIG
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = BASE_DIR / "scripts"
LOG_DIR = BASE_DIR / "logs"

LOG_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# LOGGING
# ============================================================

LOG_FILE = LOG_DIR / "security_pipeline.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# ============================================================
# PIPELINE ORDER
# ============================================================

PIPELINES = [
    "excel_parser.py",
    "employee_matching_engine.py",
    "pf_reconciliation_engine.py",
    "esi_reconciliation_engine.py",
    "wage_anomaly_detector.py",
    "compliance_risk_scoring_engine.py",
    "fraud_detection_engine.py",
    "site_performance_scoring_engine.py"
]

# ============================================================
# RUN SCRIPT
# ============================================================

def run_script(script_name):
    script_path = SCRIPTS_DIR / script_name

    if not script_path.exists():
        raise FileNotFoundError(
            f"Pipeline not found: {script_path}"
        )

    logger.info(f"Running: {script_name}")

    start_time = time.time()

    result = subprocess.run(
        ["python", str(script_path)],
        capture_output=True,
        text=True
    )

    execution_time = round(
        time.time() - start_time,
        2
    )

    if result.returncode != 0:
        logger.error(f"Failed: {script_name}")
        logger.error(result.stderr)

        raise Exception(
            f"Pipeline failed: {script_name}"
        )

    logger.info(
        f"Completed: {script_name} ({execution_time} sec)"
    )

# ============================================================
# MAIN RUNNER
# ============================================================

def run_all():

    logger.info(
        "Starting Full Security AI Pipeline"
    )

    total_start = time.time()

    for pipeline in PIPELINES:
        run_script(pipeline)

    total_time = round(
        time.time() - total_start,
        2
    )

    logger.info(
        "All Security Pipelines Completed Successfully"
    )

    logger.info(
        f"Total Execution Time: {total_time} sec"
    )

# ============================================================
# ENTRYPOINT
# ============================================================

if __name__ == "__main__":
    run_all()

