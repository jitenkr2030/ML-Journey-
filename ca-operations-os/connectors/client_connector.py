import os
import shutil
import subprocess
import logging
from pathlib import Path

# ============================================================
# BASE PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BASE_DIR.parent

CLIENTS_DIR = BASE_DIR / "data" / "clients"
BOOKKEEPING_DIR = ROOT_DIR / "bookkeeping-service"

BOOKKEEPING_RAW_DIR = BOOKKEEPING_DIR / "data" / "raw"
BOOKKEEPING_OUTPUT_DIR = BOOKKEEPING_DIR / "outputs"

PIPELINE_RUNNER = BOOKKEEPING_DIR / "pipelines" / "run_all.py"

# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# ============================================================
# VALIDATE CLIENT
# ============================================================

def validate_client(client_name):
    client_path = CLIENTS_DIR / client_name
    input_path = client_path / "input"

    if not client_path.exists():
        raise FileNotFoundError(
            f"Client folder not found: {client_path}"
        )

    if not input_path.exists():
        raise FileNotFoundError(
            f"Client input folder not found: {input_path}"
        )

    bank_file = input_path / "bank_statement.csv"
    daybook_file = input_path / "daybook.csv"

    if not bank_file.exists():
        raise FileNotFoundError(
            f"Missing bank statement: {bank_file}"
        )

    if not daybook_file.exists():
        raise FileNotFoundError(
            f"Missing daybook file: {daybook_file}"
        )

    return bank_file, daybook_file

# ============================================================
# LOAD CLIENT FILES
# ============================================================

def load_client_files(client_name):
    bank_file, daybook_file = validate_client(client_name)

    BOOKKEEPING_RAW_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    shutil.copy(
        bank_file,
        BOOKKEEPING_RAW_DIR / "bank_statement.csv"
    )

    shutil.copy(
        daybook_file,
        BOOKKEEPING_RAW_DIR / "daybook.csv"
    )

    logger.info(
        f"Loaded files for client: {client_name}"
    )

# ============================================================
# RUN BOOKKEEPING ENGINE (LIVE LOGS)
# ============================================================

def run_bookkeeping(client_name):
    env = os.environ.copy()
    env["CLIENT_NAME"] = client_name

    logger.info(
        f"Running bookkeeping pipeline for {client_name}"
    )

    result = subprocess.run(
        ["python", str(PIPELINE_RUNNER)],
        env=env,
        text=True
    )

    if result.returncode != 0:
        raise Exception(
            "Bookkeeping pipeline failed"
        )

    logger.info(
        f"Bookkeeping completed for {client_name}"
    )

# ============================================================
# SAVE CLIENT OUTPUTS
# ============================================================

def save_outputs(client_name):
    client_output_dir = CLIENTS_DIR / client_name / "output"
    client_reports_dir = CLIENTS_DIR / client_name / "reports"

    client_output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    client_reports_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    if BOOKKEEPING_OUTPUT_DIR.exists():
        if client_output_dir.exists():
            shutil.rmtree(client_output_dir)

        shutil.copytree(
            BOOKKEEPING_OUTPUT_DIR,
            client_output_dir
        )

    logger.info(
        f"Saved outputs to {client_output_dir}"
    )

# ============================================================
# MASTER PROCESS
# ============================================================

def process_client(client_name):
    logger.info(
        f"Starting client processing: {client_name}"
    )

    load_client_files(client_name)
    run_bookkeeping(client_name)
    save_outputs(client_name)

    logger.info(
        f"Completed client processing: {client_name}"
    )

# ============================================================
# ENTRYPOINT
# ============================================================

if __name__ == "__main__":
    client_name = input(
        "Enter client name: "
    ).strip()

    process_client(client_name)

