# ============================================================
# CENTRAL ACCOUNTING RULE ENGINE
# ============================================================

ACCOUNTING_RULES = {
    "Payroll": {
        "ledger": "Salary Expense",
        "journal": "Salary Expense Dr | To Bank",
        "statement": "Expense"
    },

    "Rent": {
        "ledger": "Rent Expense",
        "journal": "Rent Expense Dr | To Bank",
        "statement": "Expense"
    },

    "GST": {
        "ledger": "GST Payable",
        "journal": "GST Payable Dr | To Bank",
        "statement": "Liability"
    },

    "Asset": {
        "ledger": "Fixed Asset",
        "journal": "Fixed Asset Dr | To Bank",
        "statement": "Asset"
    },

    "Utilities": {
        "ledger": "Utilities Expense",
        "journal": "Utilities Expense Dr | To Bank",
        "statement": "Expense"
    },

    "Marketing": {
        "ledger": "Marketing Expense",
        "journal": "Marketing Expense Dr | To Bank",
        "statement": "Expense"
    },

    "Revenue": {
        "ledger": "Sales Revenue",
        "journal": "Bank Dr | To Sales Revenue",
        "statement": "Income"
    },

    "Bank Charges": {
        "ledger": "Bank Charges Expense",
        "journal": "Bank Charges Expense Dr | To Bank",
        "statement": "Expense"
    }
}


# ============================================================
# RULE FETCHER
# ============================================================

def get_accounting_rule(category):

    return ACCOUNTING_RULES.get(
        category,
        {
            "ledger": "Manual Review",
            "journal": "Manual Journal Required",
            "statement": "Unknown"
        }
    )
