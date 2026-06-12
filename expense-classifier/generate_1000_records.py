import pandas as pd
import random

print("Generating Financial Dataset...")

# Load existing dataset

df = pd.read_csv("financial_expenses_260.csv")

print("Existing Records:", len(df))

vendors = [
    "Amazon",
    "Flipkart",
    "Google",
    "Microsoft",
    "Airtel",
    "Jio",
    "BSNL",
    "Uber",
    "Ola",
    "Adobe",
    "AWS",
    "OpenAI",
    "Tata",
    "Reliance",
    "Infosys"
]

expense_types = {

    "Travel": [
        "Taxi Fare",
        "Cab Booking",
        "Flight Ticket",
        "Train Ticket",
        "Hotel Stay"
    ],

    "Utilities": [
        "Electricity Bill",
        "Water Bill",
        "Internet Bill",
        "Broadband Payment",
        "Mobile Recharge"
    ],

    "Payroll": [
        "Salary Payment",
        "Bonus Payment",
        "Staff Salary",
        "Payroll Processing",
        "Employee Benefits"
    ],

    "Office Expense": [
        "Laptop Purchase",
        "Printer Purchase",
        "Stationery Purchase",
        "Office Furniture",
        "Office Maintenance"
    ],

    "Marketing": [
        "Google Ads",
        "Facebook Ads",
        "Instagram Ads",
        "SEO Charges",
        "Marketing Campaign"
    ],

    "Rent": [
        "Office Rent",
        "Warehouse Rent",
        "Commercial Rent",
        "Property Rent"
    ],

    "Software": [
        "ChatGPT Subscription",
        "GitHub Subscription",
        "AWS Hosting",
        "Google Workspace",
        "Zoom Subscription"
    ],

    "GST": [
        "GST Payment",
        "CGST Payment",
        "SGST Payment",
        "IGST Payment"
    ],

    "Bank Charges": [
        "RTGS Charges",
        "NEFT Charges",
        "Bank Service Fee",
        "ATM Charges"
    ],

    "Vendor Payment": [
        "Vendor Payment",
        "Supplier Payment",
        "Raw Material Purchase",
        "Contractor Invoice"
    ],

    "Insurance": [
        "Health Insurance",
        "Vehicle Insurance",
        "Office Insurance",
        "Business Insurance"
    ],

    "Professional Fees": [
        "CA Fees",
        "Consulting Charges",
        "Accounting Services",
        "Professional Charges"
    ],

    "Loan Payment": [
        "Bank Loan EMI",
        "Business Loan EMI",
        "Vehicle Loan EMI"
    ],

    "TDS Payment": [
        "TDS Challan",
        "TDS Deposit",
        "TDS Payment"
    ]
}

generated_records = []

for _ in range(1000):

    category = random.choice(
        list(expense_types.keys())
    )

    description = random.choice(
        expense_types[category]
    )

    vendor = random.choice(vendors)

    amount = random.randint(
        500,
        100000
    )

    final_description = (
        f"{vendor} {description} Rs {amount}"
    )

    generated_records.append(
        [final_description, category]
    )

generated_df = pd.DataFrame(
    generated_records,
    columns=[
        "Description",
        "Category"
    ]
)

final_df = pd.concat(
    [df, generated_df],
    ignore_index=True
)

final_df = final_df.drop_duplicates()

final_df.to_csv(
    "financial_expenses_1000.csv",
    index=False
)

print("\nFinal Records:", len(final_df))

print("\nCategories:")
print(
    final_df["Category"].value_counts()
)

print("\nDataset Saved Successfully!")

print(
    "\nFile : financial_expenses_1000.csv"
)
