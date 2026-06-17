print("\nAccounting Assistant V1 - Day 15")
print("\n" + "=" * 60)
print("ACCOUNTING ASSISTANT V1")
print("=" * 60)

# SAMPLE TRANSACTIONS
transactions = [
    "Salary paid to employees",
    "Office rent paid",
    "GST payment deposited",
    "Laptop purchased for office",
    "Electricity bill paid",
    "Facebook advertisement expense",
    "Customer payment received",
    "Bank charges deducted"
]

# ACCOUNTING ENGINE
for transaction in transactions:
    transaction_lower = transaction.lower()
    
    # --------------------------------------------------------
    # PAYROLL
    # --------------------------------------------------------
    if "salary" in transaction_lower:
        category = "Payroll"
        ledger = "Salary Expense"
        journal = "Salary Expense Dr\n    To Bank"
        financial_group = "Expense"
        
    # --------------------------------------------------------
    # RENT
    # --------------------------------------------------------
    elif "rent" in transaction_lower:
        category = "Rent"
        ledger = "Rent Expense"
        journal = "Rent Expense Dr\n    To Bank"
        financial_group = "Expense"
        
    # --------------------------------------------------------
    # GST
    # --------------------------------------------------------
    elif "gst" in transaction_lower:
        category = "GST"
        ledger = "GST Payable"
        journal = "GST Payable Dr\n    To Bank"
        financial_group = "Liability"
        
    # --------------------------------------------------------
    # OFFICE ASSET
    # --------------------------------------------------------
    elif "laptop" in transaction_lower:
        category = "Asset Purchase"
        ledger = "Computer Equipment"
        journal = "Computer Equipment Dr\n    To Bank"
        financial_group = "Asset"
        
    # --------------------------------------------------------
    # ELECTRICITY
    # --------------------------------------------------------
    elif "electricity" in transaction_lower:
        category = "Utilities"
        ledger = "Electricity Expense"
        journal = "Electricity Expense Dr\n    To Bank"
        financial_group = "Expense"
        
    # --------------------------------------------------------
    # MARKETING
    # --------------------------------------------------------
    elif "advertisement" in transaction_lower:
        category = "Marketing"
        ledger = "Advertisement Expense"
        journal = "Advertisement Expense Dr\n    To Bank"
        financial_group = "Expense"
        
    # --------------------------------------------------------
    # CUSTOMER RECEIPT
    # --------------------------------------------------------
    elif "customer" in transaction_lower:
        category = "Revenue"
        ledger = "Sales Revenue"
        journal = "Bank Dr\n    To Sales Revenue"
        financial_group = "Income"
        
    # --------------------------------------------------------
    # BANK CHARGES
    # --------------------------------------------------------
    elif "bank charges" in transaction_lower:
        category = "Bank Charges"
        ledger = "Bank Charges Expense"
        journal = "Bank Charges Expense Dr\n    To Bank"
        financial_group = "Expense"
        
    # --------------------------------------------------------
    # UNKNOWN
    # --------------------------------------------------------
    else:
        category = "Unknown"
        ledger = "Manual Review"
        journal = "Manual Journal Required"
        financial_group = "Unknown"
        
    # OUTPUT
    print("\n" + "=" * 60)
    print("Transaction:", transaction)
    print("\nExpense Category:", category)
    print("\nLedger:", ledger)
    print("\nJournal Entry:\n" + journal)
    print("\nFinancial Statement Group:", financial_group)
    print("=" * 60)

print("\nAccounting Assistant V1 Completed")
print("=" * 60)
