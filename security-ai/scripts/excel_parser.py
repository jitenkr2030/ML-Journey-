import pandas as pd
import logging
from pathlib import Path
from typing import Dict

# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# ============================================================
# CONFIG
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]

RAW_DIR = BASE_DIR / "raw"
OUTPUT_DIR = BASE_DIR / "processed"

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

# ============================================================
# SHEET KEYWORDS
# ============================================================

SHEET_PATTERNS = {
    "wages": "location",
    "matching": "matching",
    "admin": "admin",
    "ecr": "ecr",
    "difference": "difference"
}

# ============================================================
# CLEAN COLUMN NAMES
# ============================================================

def clean_columns(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.replace("\n", " ", regex=False)
        .str.replace("  ", " ", regex=False)
    )
    return df


# ============================================================
# CLEAN EMPLOYEE NAMES
# ============================================================

def clean_employee_names(df: pd.DataFrame) -> pd.DataFrame:
    for col in df.columns:
        if "name" in col.lower():
            df[col] = (
                df[col]
                .astype(str)
                .str.upper()
                .str.strip()
            )
    return df


# ============================================================
# REMOVE EMPTY ROWS/COLS
# ============================================================

def remove_empty(df: pd.DataFrame) -> pd.DataFrame:
    df = df.dropna(how="all")
    df = df.dropna(axis=1, how="all")
    return df


# ============================================================
# IDENTIFY SHEETS
# ============================================================

def identify_sheets(excel_file: Path) -> Dict[str, str]:
    xls = pd.ExcelFile(excel_file)

    mapped_sheets = {}

    for sheet in xls.sheet_names:
        lower_sheet = sheet.lower()

        for key, pattern in SHEET_PATTERNS.items():
            if pattern in lower_sheet:
                mapped_sheets[key] = sheet

    return mapped_sheets


# ============================================================
# PARSE SHEET
# ============================================================

def parse_sheet(excel_file: Path, sheet_name: str):
    logger.info(f"Parsing sheet: {sheet_name}")

    df = pd.read_excel(
        excel_file,
        sheet_name=sheet_name
    )

    df = remove_empty(df)
    df = clean_columns(df)
    df = clean_employee_names(df)

    return df


# ============================================================
# SAVE CSV
# ============================================================

def save_csv(df: pd.DataFrame, file_name: str):
    output_path = OUTPUT_DIR / file_name

    df.to_csv(
        output_path,
        index=False
    )

    logger.info(f"Saved: {output_path}")


# ============================================================
# MAIN PARSER
# ============================================================

def run(excel_path: str):
    excel_file = Path(excel_path)

    if not excel_file.exists():
        raise FileNotFoundError(
            f"File not found: {excel_file}"
        )

    logger.info("Starting Excel Parsing")

    sheet_map = identify_sheets(excel_file)

    logger.info(f"Detected Sheets: {sheet_map}")

    for key, sheet_name in sheet_map.items():
        df = parse_sheet(
            excel_file,
            sheet_name
        )

        save_csv(
            df,
            f"{key}.csv"
        )

    logger.info("Excel Parsing Completed")


# ============================================================
# ENTRYPOINT
# ============================================================

if __name__ == "__main__":
    sample_file = (
        RAW_DIR /
        "pf_wages_reconciliation.xlsx"
    )

    run(sample_file)
