import os


BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

DATA_DIR = os.path.join(BASE_DIR, "data")
RAW_DIR = os.path.join(DATA_DIR, "raw")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")


# RAW INPUTS
BANK_STATEMENT_FILE = os.path.join(
    RAW_DIR,
    "bank_statement.csv"
)

DAYBOOK_FILE = os.path.join(
    RAW_DIR,
    "daybook.csv"
)

TRANSACTIONS_FILE = os.path.join(
    RAW_DIR,
    "transactions.csv"
)


# PROCESSED FILES
CLEAN_BANK_FILE = os.path.join(
    PROCESSED_DIR,
    "clean_bank_statement.csv"
)


# OUTPUT FOLDERS
ACCOUNTING_OUTPUT_DIR = os.path.join(
    OUTPUTS_DIR,
    "accounting"
)

BANKING_OUTPUT_DIR = os.path.join(
    OUTPUTS_DIR,
    "banking"
)

GST_OUTPUT_DIR = os.path.join(
    OUTPUTS_DIR,
    "gst"
)

TDS_OUTPUT_DIR = os.path.join(
    OUTPUTS_DIR,
    "tds"
)

FINANCIAL_OUTPUT_DIR = os.path.join(
    OUTPUTS_DIR,
    "financial"
)

LEDGER_OUTPUT_DIR = os.path.join(
    OUTPUTS_DIR,
    "ledgers"
)


# CREATE DIRS
for path in [
    RAW_DIR,
    PROCESSED_DIR,
    ACCOUNTING_OUTPUT_DIR,
    BANKING_OUTPUT_DIR,
    GST_OUTPUT_DIR,
    TDS_OUTPUT_DIR,
    FINANCIAL_OUTPUT_DIR,
    LEDGER_OUTPUT_DIR,
    REPORTS_DIR
]:
    os.makedirs(path, exist_ok=True)
