import joblib

print("\nAccounting Assistant CLI - Day 15")

# LOAD MODEL
print("\nLoading Model...")
model = joblib.load(
    "accounting-assistant/models/accounting_assistant_model.pkl"
)
vectorizer = joblib.load(
    "accounting-assistant/models/accounting_assistant_vectorizer.pkl"
)
print("Model Loaded Successfully!")

# CLI LOOP
while True:
    print("\n" + "=" * 60)
    
    transaction = input("\nEnter Transaction (or type exit): ")
    
    if transaction.lower() == "exit":
        print("\nExiting Accounting Assistant...")
        break
        
    # PREDICT
    vector = vectorizer.transform([transaction])
    prediction = model.predict(vector)[0]
    probability = model.predict_proba(vector)[0]
    confidence = round(max(probability) * 100, 2)
    
    # ACCOUNTING LOGIC
    if prediction == "Payroll":
        ledger = "Salary Expense"
        journal = "Salary Expense Dr\n    To Bank"
        statement = "Expense"
    elif prediction == "Rent":
        ledger = "Rent Expense"
        journal = "Rent Expense Dr\n    To Bank"
        statement = "Expense"
    elif prediction == "GST":
        ledger = "GST Payable"
        journal = "GST Payable Dr\n    To Bank"
        statement = "Liability"
    elif prediction == "Asset":
        ledger = "Fixed Assets"
        journal = "Fixed Asset Dr\n    To Bank"
        statement = "Asset"
    elif prediction == "Utilities":
        ledger = "Utilities Expense"
        journal = "Utilities Expense Dr\n    To Bank"
        statement = "Expense"
    elif prediction == "Marketing":
        ledger = "Advertisement Expense"
        journal = "Advertisement Expense Dr\n    To Bank"
        statement = "Expense"
    elif prediction == "Revenue":
        ledger = "Sales Revenue"
        journal = "Bank Dr\n    To Sales Revenue"
        statement = "Income"
    elif prediction == "Bank Charges":
        ledger = "Bank Charges Expense"
        journal = "Bank Charges Expense Dr\n    To Bank"
        statement = "Expense"
    elif prediction == "Loan":
        ledger = "Loan Payable"
        journal = "Loan Payable Dr\n    To Bank"
        statement = "Liability"
    elif prediction == "Insurance":
        ledger = "Insurance Expense"
        journal = "Insurance Expense Dr\n    To Bank"
        statement = "Expense"
    elif prediction == "Professional Fees":
        ledger = "Professional Fees Expense"
        journal = "Professional Fees Expense Dr\n    To Bank"
        statement = "Expense"
    elif prediction == "Travel":
        ledger = "Travel Expense"
        journal = "Travel Expense Dr\n    To Bank"
        statement = "Expense"
    else:
        ledger = "Manual Review"
        journal = "Manual Journal Required"
        statement = "Unknown"
        
    # OUTPUT
    print("\n" + "=" * 60)
    print("ACCOUNTING ASSISTANT RESULT")
    print("=" * 60)
    print("\nTransaction:", transaction)
    print("\nPredicted Category:", prediction)
    print("\nConfidence:", confidence, "%")
    print("\nLedger:", ledger)
    print("\nJournal Entry:\n" + journal)
    print("\nFinancial Statement Group:", statement)
    print("\n" + "=" * 60)

print("\nDay 15 CLI Completed Successfully!")
