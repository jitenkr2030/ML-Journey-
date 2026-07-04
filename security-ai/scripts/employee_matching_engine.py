import pandas as pd
import logging
import re
from pathlib import Path
from rapidfuzz import fuzz, process

# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# ============================================================
# PATH CONFIG
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]

INPUT_DIR = BASE_DIR / "processed"
OUTPUT_DIR = BASE_DIR / "reconciliation"

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

WAGES_FILE = INPUT_DIR / "wages.csv"
PF_FILE = INPUT_DIR / "pf.csv"
ESI_FILE = INPUT_DIR / "esi.csv"
BANK_FILE = INPUT_DIR / "bank.csv"

OUTPUT_FILE = OUTPUT_DIR / "employee_matching_report.csv"

# ============================================================
# NORMALIZATION
# ============================================================

def normalize_name(name):
    if pd.isna(name):
        return ""

    name = str(name).lower().strip()

    name = re.sub(r"[^a-zA-Z\s]", "", name)

    name = re.sub(r"\s+", " ", name)

    stop_words = [
        "so",
        "s/o",
        "d/o",
        "w/o"
    ]

    words = []

    for word in name.split():
        if word not in stop_words:
            words.append(word)

    return " ".join(words)

# ============================================================
# LOAD FILES
# ============================================================

def safe_load(file_path):
    if not file_path.exists():
        logger.warning(f"Missing file: {file_path}")
        return pd.DataFrame()

    return pd.read_csv(file_path)

# ============================================================
# EXTRACT EMPLOYEE NAMES
# ============================================================

def extract_names(df, column_name):
    if df.empty:
        return []

    if column_name not in df.columns:
        return []

    return df[column_name].dropna().tolist()

# ============================================================
# FUZZY MATCH
# ============================================================

def fuzzy_match(source_name, target_names):
    result = process.extractOne(
        source_name,
        target_names,
        scorer=fuzz.token_sort_ratio
    )

    if result:
        matched_name, score, _ = result
        return matched_name, score

    return None, 0

# ============================================================
# BUILD MATCH REPORT
# ============================================================

def build_matching_report():
    wages_df = safe_load(WAGES_FILE)
    pf_df = safe_load(PF_FILE)
    esi_df = safe_load(ESI_FILE)
    bank_df = safe_load(BANK_FILE)

    wage_names = extract_names(
        wages_df,
        "NAME"
    )

    pf_names = extract_names(
        pf_df,
        "NAME"
    )

    esi_names = extract_names(
        esi_df,
        "NAME"
    )

    bank_names = extract_names(
        bank_df,
        "NAME"
    )

    normalized_pf = {
        normalize_name(name): name
        for name in pf_names
    }

    normalized_esi = {
        normalize_name(name): name
        for name in esi_names
    }

    normalized_bank = {
        normalize_name(name): name
        for name in bank_names
    }

    rows = []

    for wage_name in wage_names:
        clean_wage_name = normalize_name(
            wage_name
        )

        # PF Match
        pf_match, pf_score = fuzzy_match(
            clean_wage_name,
            list(normalized_pf.keys())
        )

        # ESI Match
        esi_match, esi_score = fuzzy_match(
            clean_wage_name,
            list(normalized_esi.keys())
        )

        # Bank Match
        bank_match, bank_score = fuzzy_match(
            clean_wage_name,
            list(normalized_bank.keys())
        )

        rows.append({
            "Wage_Name": wage_name,

            "PF_Match":
                normalized_pf.get(pf_match, ""),
            "PF_Confidence":
                pf_score,

            "ESI_Match":
                normalized_esi.get(esi_match, ""),
            "ESI_Confidence":
                esi_score,

            "Bank_Match":
                normalized_bank.get(bank_match, ""),
            "Bank_Confidence":
                bank_score
        })

    return pd.DataFrame(rows)

# ============================================================
# FLAG RISKS
# ============================================================

def apply_match_risk_flags(df):
    risk_flags = []

    for _, row in df.iterrows():
        risks = []

        if row["PF_Confidence"] < 80:
            risks.append("PF Mismatch")

        if row["ESI_Confidence"] < 80:
            risks.append("ESI Mismatch")

        if row["Bank_Confidence"] < 80:
            risks.append("Bank Mismatch")

        if not risks:
            risks.append("Matched")

        risk_flags.append(
            ", ".join(risks)
        )

    df["Match_Status"] = risk_flags

    return df

# ============================================================
# SAVE
# ============================================================

def save_report(df):
    df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    logger.info(
        f"Saved: {OUTPUT_FILE}"
    )

# ============================================================
# MAIN
# ============================================================

def run():
    logger.info(
        "Starting Employee Matching Engine"
    )

    report_df = build_matching_report()

    if report_df.empty:
        logger.warning(
            "No matching data found"
        )
        return

    report_df = apply_match_risk_flags(
        report_df
    )

    save_report(
        report_df
    )

    logger.info(
        "Employee Matching Engine Completed"
    )

# ============================================================
# ENTRYPOINT
# ============================================================

if __name__ == "__main__":
    run()
