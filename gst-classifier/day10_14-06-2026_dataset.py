import pandas as pd
import random

print("\nGenerating GST Invoice Dataset...")

categories = {

    "B2B": [
        "Sale Invoice to ABC Pvt Ltd",
        "Invoice to XYZ Industries",
        "GST Invoice to Corporate Client",
        "B2B Supply Invoice",
        "Wholesale Sale Invoice"
    ],

    "B2C": [
        "Retail Customer Invoice",
        "Consumer Sale Bill",
        "GST Cash Memo",
        "Store Sale Invoice",
        "Customer Purchase Invoice"
    ],

    "Export": [
        "Export Invoice USA",
        "Export Sale UK",
        "International Export Invoice",
        "Export Shipment Invoice",
        "Overseas Customer Invoice"
    ],

    "Import": [
        "Import Purchase China",
        "Import Goods Invoice",
        "International Vendor Invoice",
        "Import Material Purchase",
        "Overseas Supplier Invoice"
    ],

    "Credit Note": [
        "GST Credit Note",
        "Sales Return Credit Note",
        "Customer Refund Credit Note",
        "Credit Adjustment Note",
        "Product Return Credit Note"
    ],

    "Debit Note": [
        "GST Debit Note",
        "Purchase Debit Note",
        "Supplier Debit Adjustment",
        "Additional Charge Debit Note",
        "Debit Adjustment Invoice"
    ],

    "GST Payment": [
        "GST Challan Payment",
        "CGST Payment",
        "SGST Payment",
        "IGST Payment",
        "GST Liability Payment"
    ],

    "GST Refund": [
        "GST Refund Claim",
        "Refund Application Invoice",
        "GST Refund Processing",
        "Input Tax Refund",
        "Refund Settlement"
    ],

    "Reverse Charge": [
        "Reverse Charge GST Invoice",
        "RCM Purchase Invoice",
        "Legal Service Reverse Charge",
        "Transport Reverse Charge",
        "RCM Vendor Invoice"
    ],

    "Exempt Supply": [
        "GST Exempt Supply Invoice",
        "Exempt Service Bill",
        "Nil Rated Supply Invoice",
        "Exempt Goods Sale",
        "Tax Free Supply Invoice"
    ]
}

companies = [
    "Infosys",
    "TCS",
    "Wipro",
    "HCL",
    "Reliance",
    "Airtel",
    "Jio",
    "Amazon",
    "Flipkart",
    "Google"
]

records = []

for category, invoices in categories.items():

    for i in range(60):

        invoice = random.choice(invoices)

        company = random.choice(companies)

        amount = random.randint(1000, 100000)

        description = f"{company} {invoice} Rs {amount}"

        records.append(
            [description, category]
        )

df = pd.DataFrame(
    records,
    columns=[
        "Invoice_Text",
        "Category"
    ]
)

output_file = "gst-classifier/datasets/gst_invoices_600.csv"

df.to_csv(
    output_file,
    index=False
)

print("\nDataset Created Successfully!")
print("Total Records :", len(df))
print("File :", output_file)

print("\nSample Data:")
print(df.head())
