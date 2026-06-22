import os
import re
import logging
import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

OUTPUTS_DIR = "bookkeeping-service/outputs"

INPUT_FILE = os.path.join(
    OUTPUTS_DIR,
    "accounting_output.csv"
)

OUTPUT_FILE = os.path.join(
    OUTPUTS_DIR,
    "tds_output.csv"
)

SUMMARY_FILE = os.path.join(
    OUTPUTS_DIR,
    "tds_summary.csv"
)

MANUAL_REVIEW_FILE = os.path.join(
    OUTPUTS_DIR,
    "tds_manual_review.csv"
)


# ============================================================
# TDS RULES
# ============================================================

TDS_RULES = {

    "194C": {
        "keywords": ["contract", "labour"],
        "threshold": 30000,
        "rate": 1
    },

    "194J": {
        "keywords": ["professional", "consultant"],
        "threshold": 30000,
        "rate": 10
    },

    "194H": {
        "keywords": ["commission", "brokerage"],
        "threshold": 15000,
        "rate": 5
    },

    "194I": {
        "keywords": ["rent"],
        "threshold": 240000,
        "rate": 10
    },

    "194Q": {
        "keywords": ["purchase"],
        "threshold": 5000000,
        "rate": 0.1
    }

}


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


# ============================================================
# LOAD DATA
# ============================================================

def load_data():

    if not os.path.exists(INPUT_FILE):
        raise FileNotFoundError(
            f"Missing accounting file: {INPUT_FILE}"
        )

    df = pd.read_csv(
        INPUT_FILE
    )

    required_cols = [
        "Transaction_Text",
        "Amount"
    ]

    for col in required_cols:
        if col not in df.columns:
            raise ValueError(
                f"Missing required column: {col}"
            )

    logging.info(
        f"Loaded {len(df)} records"
    )

    return df


# ============================================================
# PAN VALIDATION
# ============================================================

def validate_pan(text):

    pattern = r'[A-Z]{5}[0-9]{4}[A-Z]{1}'

    if re.search(pattern, str(text)):
        return "Valid"

    return "Missing"


# ============================================================
# DETECT TDS SECTION
# ============================================================

def detect_tds_section(text):

    text = str(text).lower()

    for section, rule in TDS_RULES.items():

        for keyword in rule["keywords"]:

            if keyword in text:
                return section

    return "No TDS"


# ============================================================
# PROCESS TDS
# ============================================================

def process_tds(df):

    sections = []
    thresholds = []
    rates = []
    tds_amounts = []
    pan_statuses = []
    compliance_flags = []

    for _, row in df.iterrows():

        text = row["Transaction_Text"]
        amount = float(row["Amount"])

        section = detect_tds_section(
            text
        )

        pan_status = validate_pan(
            text
        )

        if section == "No TDS":

            threshold = 0
            rate = 0
            tds_amount = 0
            compliance = "OK"

        else:

            threshold = TDS_RULES[
                section
            ]["threshold"]

            rate = TDS_RULES[
                section
            ]["rate"]

            if amount >= threshold:

                tds_amount = (
                    amount * rate
                ) / 100

                compliance = "Deduct TDS"

            else:

                tds_amount = 0
                compliance = "Below Threshold"

            if pan_status == "Missing":
                compliance = "PAN Required"

        sections.append(
            section
        )

        thresholds.append(
            threshold
        )

        rates.append(
            rate
        )

        tds_amounts.append(
            round(tds_amount, 2)
        )

        pan_statuses.append(
            pan_status
        )

        compliance_flags.append(
            compliance
        )

    df["TDS_Section"] = sections
    df["Threshold"] = thresholds
    df["TDS_Rate"] = rates
    df["TDS_Amount"] = tds_amounts
    df["PAN_Status"] = pan_statuses
    df["Compliance_Status"] = compliance_flags

    return df


# ============================================================
# SUMMARY
# ============================================================

def generate_summary(df):

    summary = df.groupby(
        "TDS_Section"
    )["TDS_Amount"].sum().reset_index()

    summary.columns = [
        "TDS_Section",
        "Total_TDS"
    ]

    return summary


# ============================================================
# SAVE OUTPUTS
# ============================================================

def save_outputs(df, summary):

    df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    summary.to_csv(
        SUMMARY_FILE,
        index=False
    )

    review_df = df[
        df["Compliance_Status"].isin(
            ["PAN Required"]
        )
    ]

    review_df.to_csv(
        MANUAL_REVIEW_FILE,
        index=False
    )

    logging.info(
        f"TDS output saved: {OUTPUT_FILE}"
    )

    logging.info(
        f"TDS summary saved: {SUMMARY_FILE}"
    )

    logging.info(
        f"TDS manual review saved: {MANUAL_REVIEW_FILE}"
    )


# ============================================================
# MAIN
# ============================================================

def run_pipeline():

    logging.info(
        "Starting TDS Pipeline"
    )

    df = load_data()

    processed_df = process_tds(
        df
    )

    summary_df = generate_summary(
        processed_df
    )

    save_outputs(
        processed_df,
        summary_df
    )

    logging.info(
        "TDS Pipeline Completed"
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    run_pipeline()

