import joblib

print("\n" + "=" * 60)
print("FINANCIAL STATEMENT AI CLI - DAY 15")
print("=" * 60)

print("\nLoading Model...")
model = joblib.load(
    "financial-statement-ai/models/financial_statement_model.pkl"
)
vectorizer = joblib.load(
    "financial-statement-ai/models/financial_statement_vectorizer.pkl"
)
print("Model Loaded Successfully!")

while True:
    print("\n" + "=" * 60)
    
    account_name = input("\nEnter Account Name (or type exit): ")
    
    if account_name.lower() == "exit":
        print("\nClosing Financial Statement AI...")
        break
        
    account_vector = vectorizer.transform([account_name])
    prediction = model.predict(account_vector)[0]
    probabilities = model.predict_proba(account_vector)[0]
    confidence = max(probabilities) * 100
    
    print("\nPrediction :", prediction)
    print("Confidence :", round(confidence, 2), "%")
    print("\nFinancial Interpretation")
    
    if prediction == "Asset":
        print("- Appears in Balance Sheet")
        print("- Represents resources owned by business")
        print("- Examples: Cash, Bank, Inventory")
    elif prediction == "Liability":
        print("- Appears in Balance Sheet")
        print("- Represents obligations/payables")
        print("- Examples: GST Payable, Loan Payable")
    elif prediction == "Income":
        print("- Appears in Profit & Loss Statement")
        print("- Increases business profit")
        print("- Examples: Sales Revenue, Service Revenue")
    elif prediction == "Expense":
        print("- Appears in Profit & Loss Statement")
        print("- Reduces business profit")
        print("- Examples: Salary Expense, Rent Expense")
    else:
        print("- Unknown Account Group")
        
    print("\n" + "-" * 60)

print("\nDay 15 CLI Completed Successfully!")
