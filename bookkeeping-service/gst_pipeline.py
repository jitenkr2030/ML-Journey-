import os
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
    "gst_output.csv"
)

SUMMARY_FILE = os.path.join(
    OUTPUTS_DIR,
    "gst_summary.csv"
)

MANUAL_REVIEW_FILE = os.path.join(
    OUTPUTS_DIR,
    "gst_manual_review.csv"
)

GST_RATE = 18


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
        "Amount",
        "Predicted_Category"
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
# GST CLASSIFICATION
# ============================================================

def classify_gst(df):

    gst_types = []
    gst_amounts = []
    cgst_amounts = []
    sgst_amounts = []
    review_flags = []

    for _, row in df.iterrows():

        category = str(
            row["Predicted_Category"]
        )

        amount = float(
            row["Amount"]
        )

        text = str(
            row["Transaction_Text"]
        ).lower()

        gst_type = "Exempt"
        gst_amount = 0
        cgst = 0
        sgst = 0
        review = "OK"

        # OUTPUT GST
        if category == "Revenue":

            gst_type = "Output GST"

            gst_amount = amount * GST_RATE / 100
            cgst = gst_amount / 2
            sgst = gst_amount / 2

        # INPUT GST
        elif category in [
            "Asset",
            "Rent",
            "Utilities",
            "Marketing"
        ]:

            gst_type = "Input GST"

            gst_amount = amount * GST_RATE / 100
            cgst = gst_amount / 2
            sgst = gst_amount / 2

        # RCM Detection
        if "rcm" in text:
            gst_type = "RCM"

            gst_amount = amount * GST_RATE / 100
            cgst = gst_amount / 2
            sgst = gst_amount / 2

        # Zero Rated
        if "export" in text:
            gst_type = "Zero Rated"
            gst_amount = 0
            cgst = 0
            sgst = 0

        # Manual Review
        if amount <= 0:
            review = "REVIEW"

        gst_types.append(
            gst_type
        )

        gst_amounts.append(
            round(gst_amount, 2)
        )

        cgst_amounts.append(
            round(cgst, 2)
        )

        sgst_amounts.append(
            round(sgst, 2)
        )

        review_flags.append(
            review
        )

    df["GST_Type"] = gst_types
    df["GST_Amount"] = gst_amounts
    df["CGST"] = cgst_amounts
    df["SGST"] = sgst_amounts
    df["GST_Status"] = review_flags

    return df


# ============================================================
# GST SUMMARY
# ============================================================

def generate_summary(df):

    summary = df.groupby(
        "GST_Type"
    )["GST_Amount"].sum().reset_index()

    summary.columns = [
        "GST_Type",
        "Total_GST"
    ]

    return summary


# ============================================================
# SAVE OUTPUTS
# ============================================================

def save_outputs(df, summary):

    os.makedirs(
        OUTPUTS_DIR,
        exist_ok=True
    )

    df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    summary.to_csv(
        SUMMARY_FILE,
        index=False
    )

    review_df = df[
        df["GST_Status"] == "REVIEW"
    ]

    review_df.to_csv(
        MANUAL_REVIEW_FILE,
        index=False
    )

    logging.info(
        f"GST output saved: {OUTPUT_FILE}"
    )

    logging.info(
        f"GST summary saved: {SUMMARY_FILE}"
    )

    logging.info(
        f"GST manual review saved: {MANUAL_REVIEW_FILE}"
    )


# ============================================================
# MAIN
# ============================================================

def run_pipeline():

    logging.info(
        "Starting GST Pipeline"
    )

    df = load_data()

    gst_df = classify_gst(
        df
    )

    summary_df = generate_summary(
        gst_df
    )

    save_outputs(
        gst_df,
        summary_df
    )

    logging.info(
        "GST Pipeline Completed"
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    run_pipeline()

