import os
import logging
import pandas as pd
from pathlib import Path
import sys

# ============================================================
# PATH SETUP
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]
client_name = os.getenv("CLIENT_NAME", "client1")
CLIENT_DIR = Path("ca-operations-os/data/clients")
sys.path.append(str(BASE_DIR))

from core.closing_rules import get_closing_checklist

OUTPUT_DIR = CLIENT_DIR / client_name / "output"
FINANCIAL_DIR = OUTPUT_DIR / "financial"
OUTPUT_FILE = FINANCIAL_DIR / "closing_checklist.csv"

FINANCIAL_DIR.mkdir(
    parents=True,
    exist_ok=True
)

# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# ============================================================
# BUILD CHECKLIST
# ============================================================

def build_checklist():
    checklist_rules = get_closing_checklist()

    checklist = []

    for item in checklist_rules:
        file_path = BASE_DIR / item["path"]

        status = (
            "Completed"
            if file_path.exists()
            else "Pending"
        )

        checklist.append({
            "Task": item["task"],
            "Status": status,
            "File": file_path.name
        })

    return pd.DataFrame(checklist)

# ============================================================
# SAVE
# ============================================================

def save_checklist(df):
    df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    logger.info(
        f"Closing checklist saved: {OUTPUT_FILE}"
    )

# ============================================================
# MAIN
# ============================================================

def run():
    logger.info(
        "Starting Closing Checklist Pipeline"
    )

    checklist_df = build_checklist()
    save_checklist(checklist_df)

    logger.info(
        "Closing Checklist Pipeline Completed"
    )

# ============================================================
# ENTRYPOINT
# ============================================================

if __name__ == "__main__":
    run()
