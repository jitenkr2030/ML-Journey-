import os
import logging
import pandas as pd
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
client_name = os.getenv("CLIENT_NAME", "client1")
CLIENT_DIR = Path("ca-operations-os/data/clients")
sys.path.append(str(BASE_DIR))

from config.paths import FINANCIAL_OUTPUT_DIR

P_AND_L_FILE = Path(FINANCIAL_OUTPUT_DIR) / "profit_and_loss.csv"
BALANCE_SHEET_FILE = Path(FINANCIAL_OUTPUT_DIR) / "balance_sheet.csv"
RATIO_FILE = Path(FINANCIAL_OUTPUT_DIR) / "financial_ratios.csv"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def load_files():
    if not P_AND_L_FILE.exists():
        raise FileNotFoundError(
            f"Missing file: {P_AND_L_FILE}"
        )

    if not BALANCE_SHEET_FILE.exists():
        raise FileNotFoundError(
            f"Missing file: {BALANCE_SHEET_FILE}"
        )

    return (
        pd.read_csv(P_AND_L_FILE),
        pd.read_csv(BALANCE_SHEET_FILE)
    )


def get_value(df, key):
    row = df.loc[
        df["Particulars"] == key,
        "Amount"
    ]

    if row.empty:
        return 0.0

    return float(row.values[0])


def safe_divide(a, b):
    if b == 0:
        return 0.0

    return round(a / b, 4)


def calculate_ratios(pnl_df, bs_df):
    revenue = get_value(pnl_df, "Revenue")
    expenses = get_value(pnl_df, "Expenses")
    gross_profit = get_value(pnl_df, "Gross Profit")
    net_profit = get_value(pnl_df, "Net Profit")

    assets = get_value(bs_df, "Assets")
    liabilities = get_value(bs_df, "Liabilities")
    capital = get_value(bs_df, "Capital")

    return pd.DataFrame([
        ["Gross Profit Ratio (%)", safe_divide(gross_profit, revenue) * 100],
        ["Net Profit Ratio (%)", safe_divide(net_profit, revenue) * 100],
        ["Expense Ratio (%)", safe_divide(expenses, revenue) * 100],
        ["Current Ratio", safe_divide(assets, liabilities)],
        ["Debt Equity Ratio", safe_divide(liabilities, capital)],
        ["Asset Turnover Ratio", safe_divide(revenue, assets)]
    ], columns=["Ratio", "Value"])


def save_output(df):
    df.to_csv(
        RATIO_FILE,
        index=False
    )

    logger.info(
        f"Ratio analysis saved: {RATIO_FILE}"
    )


def run():
    logger.info(
        "Starting Ratio Analysis"
    )

    pnl_df, bs_df = load_files()

    ratio_df = calculate_ratios(
        pnl_df,
        bs_df
    )

    save_output(ratio_df)

    logger.info(
        "Ratio Analysis Completed"
    )


if __name__ == "__main__":
    run()
