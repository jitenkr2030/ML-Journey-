import pandas as pd

print("\nFinancial Statement AI - Day 15")

# ============================================================
# LOAD DATASET
# ============================================================

print("\nLoading Dataset...")

df = pd.read_csv(
    "financial-statement-ai/datasets/financial_statements_5200.csv"
)

print("\nDataset Preview:")
print(df.head())

print("\nTotal Records :", len(df))

# ============================================================
# TRIAL BALANCE
# ============================================================

print("\n" + "=" * 60)
print("TRIAL BALANCE")
print("=" * 60)

trial_balance = df.groupby(
    "Account_Name"
)[["Debit", "Credit"]].sum()

print(trial_balance)

# ============================================================
# ACCOUNT GROUPS
# ============================================================

assets = [
    "Cash",
    "Bank Account",
    "Accounts Receivable",
    "Inventory",
    "Furniture",
    "Computer Equipment",
    "Vehicle"
]

liabilities = [
    "Accounts Payable",
    "GST Payable",
    "Loan Payable"
]

income = [
    "Sales Revenue",
    "Service Revenue",
    "Commission Income"
]

expenses = [
    "Salary Expense",
    "Rent Expense",
    "Electricity Expense",
    "Internet Expense",
    "Marketing Expense"
]

# ============================================================
# TOTALS
# ============================================================

total_assets = df[
    df["Account_Name"].isin(assets)
]["Debit"].sum()

total_liabilities = df[
    df["Account_Name"].isin(liabilities)
]["Credit"].sum()

total_income = df[
    df["Account_Name"].isin(income)
]["Credit"].sum()

total_expenses = df[
    df["Account_Name"].isin(expenses)
]["Debit"].sum()

net_profit = total_income - total_expenses

# ============================================================
# FINANCIAL STATEMENT
# ============================================================

print("\n" + "=" * 60)
print("FINANCIAL STATEMENT SUMMARY")
print("=" * 60)

print("\nTotal Assets      :", round(total_assets, 2))
print("Total Liabilities :", round(total_liabilities, 2))
print("Total Income      :", round(total_income, 2))
print("Total Expenses    :", round(total_expenses, 2))
print("Net Profit        :", round(net_profit, 2))

# ============================================================
# BALANCE SHEET
# ============================================================

balance_sheet = pd.DataFrame({

    "Particulars": [
        "Total Assets",
        "Total Liabilities",
        "Net Profit"
    ],

    "Amount": [
        total_assets,
        total_liabilities,
        net_profit
    ]
})

print("\n" + "=" * 60)
print("BALANCE SHEET")
print("=" * 60)

print(balance_sheet)

# ============================================================
# SAVE REPORT
# ============================================================

balance_sheet.to_csv(
    "financial-statement-ai/results_day15.csv",
    index=False
)

print("\nResults Saved Successfully!")

print("\nDay 15 Completed Successfully!")
