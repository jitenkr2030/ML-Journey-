import os
import logging
import pandas as pd


# ============================================================
# CONFIG
# ============================================================

OUTPUTS_DIR = "bookkeeping-service/outputs"

INPUT_FILE = os.path.join(
    OUTPUTS_DIR,
    "accounting_output.csv"
)

P_AND_L_FILE = os.path.join(
    OUTPUTS_DIR,
    "profit_and_loss.csv"
)

BALANCE_SHEET_FILE = os.path.join(
    OUTPUTS_DIR,
    "balance_sheet.csv"
)

TRIAL_BALANCE_FILE = os.path.join(
    OUTPUTS_DIR,
    "trial_balance.csv"
)

CASHFLOW_FILE = os.path.join(
    OUTPUTS_DIR,
    "cash_flow.csv"
)


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
            f"Missing file: {INPUT_FILE}"
        )

    df = pd.read_csv(INPUT_FILE)

    required_cols = [
        "Transaction_Text",
        "Amount",
        "Predicted_Category",
        "Ledger",
        "Financial_Statement"
    ]

    for col in required_cols:
        if col not in df.columns:
            raise ValueError(
                f"Missing required column: {col}"
            )

    logging.info(
        f"Loaded {len(df)} accounting entries"
    )

    return df


# ============================================================
# PROFIT & LOSS
# ============================================================

def generate_p_and_l(df):

    revenue = df[
        df["Predicted_Category"] == "Revenue"
    ]["Amount"].sum()

    expenses = df[
        df["Financial_Statement"] == "Expense"
    ]["Amount"].sum()

    gross_profit = revenue - expenses
    net_profit = gross_profit

    pnl = pd.DataFrame([
        ["Revenue", revenue],
        ["Expenses", expenses],
        ["Gross Profit", gross_profit],
        ["Net Profit", net_profit]
    ], columns=["Particulars", "Amount"])

    return pnl


# ============================================================
# BALANCE SHEET
# ============================================================

def generate_balance_sheet(df):

    assets = df[
        df["Financial_Statement"] == "Asset"
    ]["Amount"].sum()

    liabilities = df[
        df["Financial_Statement"] == "Liability"
    ]["Amount"].sum()

    capital = assets - liabilities

    balance_sheet = pd.DataFrame([
        ["Assets", assets],
        ["Liabilities", liabilities],
        ["Capital", capital]
    ], columns=["Particulars", "Amount"])

    return balance_sheet


# ============================================================
# TRIAL BALANCE
# ============================================================

def generate_trial_balance(df):

    trial = df.groupby(
        "Ledger"
    )["Amount"].sum().reset_index()

    trial.columns = [
        "Ledger",
        "Balance"
    ]

    return trial


# ============================================================
# CASH FLOW
# ============================================================

def generate_cash_flow(df):

    operating_cash = df[
        df["Predicted_Category"].isin(
            [
                "Revenue",
                "Payroll",
                "Rent",
                "Utilities",
                "Marketing"
            ]
        )
    ]["Amount"].sum()

    investing_cash = df[
        df["Predicted_Category"] == "Asset"
    ]["Amount"].sum()

    financing_cash = df[
        df["Predicted_Category"] == "Loan"
    ]["Amount"].sum()

    cash_flow = pd.DataFrame([
        ["Operating Cash Flow", operating_cash],
        ["Investing Cash Flow", investing_cash],
        ["Financing Cash Flow", financing_cash]
    ], columns=["Particulars", "Amount"])

    return cash_flow


# ============================================================
# SAVE OUTPUTS
# ============================================================

def save_outputs(
    pnl,
    balance_sheet,
    trial_balance,
    cash_flow
):

    pnl.to_csv(
        P_AND_L_FILE,
        index=False
    )

    balance_sheet.to_csv(
        BALANCE_SHEET_FILE,
        index=False
    )

    trial_balance.to_csv(
        TRIAL_BALANCE_FILE,
        index=False
    )

    cash_flow.to_csv(
        CASHFLOW_FILE,
        index=False
    )

    logging.info(
        f"P&L saved: {P_AND_L_FILE}"
    )

    logging.info(
        f"Balance Sheet saved: {BALANCE_SHEET_FILE}"
    )

    logging.info(
        f"Trial Balance saved: {TRIAL_BALANCE_FILE}"
    )

    logging.info(
        f"Cash Flow saved: {CASHFLOW_FILE}"
    )


# ============================================================
# MAIN
# ============================================================

def run_pipeline():

    logging.info(
        "Starting Financial Statement Pipeline"
    )

    df = load_data()

    pnl = generate_p_and_l(df)

    balance_sheet = generate_balance_sheet(df)

    trial_balance = generate_trial_balance(df)

    cash_flow = generate_cash_flow(df)

    save_outputs(
        pnl,
        balance_sheet,
        trial_balance,
        cash_flow
    )

    logging.info(
        "Financial Statement Pipeline Completed"
    )


# ============================================================
# ENTRY
# ============================================================

if __name__ == "__main__":
    run_pipeline()

