import pandas as pd
import logging
from pathlib import Path
from sklearn.ensemble import IsolationForest

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

OUTPUT_FILE = OUTPUT_DIR / "wage_anomaly_report.csv"

# ============================================================
# LOAD DATA
# ============================================================

def load_wages():
    if not WAGES_FILE.exists():
        logger.error(f"Missing file: {WAGES_FILE}")
        return pd.DataFrame()

    return pd.read_csv(WAGES_FILE)

# ============================================================
# FEATURE ENGINEERING
# ============================================================

def prepare_features(df):
    features = pd.DataFrame()

    features["days_worked"] = df["No Of Days Worked"]
    features["overtime_hours"] = df["Overtime Hours Worked"]
    features["basic_vda"] = df["BASIC + VDA"]
    features["total_salary"] = df["TOTAL"]
    features["pf"] = df["EPF 12% of15000 if BASIC + VDA IS ABOVE 15000"]
    features["esi"] = df["ESIC 0.75% OF BASIC +VDA"]
    features["recoveries"] = df["Recoveries"]
    features["net_payment"] = df["NET PAYMENT"]

    return features.fillna(0)

# ============================================================
# ANOMALY DETECTION
# ============================================================

def detect_anomalies(df):
    feature_df = prepare_features(df)

    model = IsolationForest(
        contamination=0.05,
        random_state=42
    )

    predictions = model.fit_predict(
        feature_df
    )

    df["Anomaly_Flag"] = predictions

    df["Risk_Status"] = df["Anomaly_Flag"].apply(
        lambda x: "High Risk" if x == -1 else "Normal"
    )

    return df

# ============================================================
# RULE BASED FLAGS
# ============================================================

def apply_business_rules(df):
    risk_notes = []

    for _, row in df.iterrows():
        notes = []

        if row["Overtime Hours Worked"] > 50:
            notes.append("Excessive Overtime")

        if row["No Of Days Worked"] > 31:
            notes.append("Invalid Working Days")

        if row["BASIC + VDA"] == 0:
            notes.append("Zero Wage")

        if row["NET PAYMENT"] > row["TOTAL"]:
            notes.append("Net Pay Higher Than Gross")

        if row["Recoveries"] > row["TOTAL"] * 0.50:
            notes.append("High Recoveries")

        if not notes:
            notes.append("No Risk")

        risk_notes.append(
            ", ".join(notes)
        )

    df["Business_Risk_Notes"] = risk_notes

    return df

# ============================================================
# SAVE REPORT
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
        "Starting Wage Anomaly Detection"
    )

    wages_df = load_wages()

    if wages_df.empty:
        return

    wages_df = detect_anomalies(
        wages_df
    )

    wages_df = apply_business_rules(
        wages_df
    )

    save_report(
        wages_df
    )

    logger.info(
        "Wage Anomaly Detection Completed"
    )

# ============================================================
# ENTRYPOINT
# ============================================================

if __name__ == "__main__":
    run()
