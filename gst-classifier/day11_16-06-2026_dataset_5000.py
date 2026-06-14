import pandas as pd
import random

print("\nGenerating GST Invoice Dataset (5000 Records)...")

companies = [
    "ABC Pvt Ltd",
    "XYZ Industries",
    "TCS",
    "Infosys",
    "Wipro",
    "HCL",
    "Reliance",
    "Tata Steel",
    "Flipkart",
    "Amazon",
    "Google",
    "Microsoft",
    "Accenture",
    "Deloitte",
    "Tech Mahindra"
]

countries = [
    "USA",
    "UK",
    "Canada",
    "Australia",
    "Germany",
    "Japan",
    "Singapore",
    "France",
    "China",
    "South Korea"
]

states = [
    "Delhi",
    "Maharashtra",
    "Karnataka",
    "Tamil Nadu",
    "Gujarat",
    "Rajasthan",
    "Punjab",
    "Haryana"
]

categories = {

    "B2B": [
        "Invoice to {}",
        "Wholesale supply to {}",
        "Corporate software license for {}",
        "GST invoice raised on {}",
        "Supply of goods to {}"
    ],

    "B2C": [
        "Retail customer purchase bill",
        "Cash sale invoice",
        "Consumer electronics invoice",
        "Mobile phone sale bill",
        "Walk-in customer invoice"
    ],

    "Export": [
        "Export software service to {}",
        "Consulting invoice to {}",
        "Export of garments to {}",
        "IT support service to {}",
        "International client invoice {}"
    ],

    "Import": [
        "Import machinery from {}",
        "Import electronics from {}",
        "Raw material imported from {}",
        "Hardware purchase from {}",
        "Industrial equipment imported from {}"
    ],

    "Credit Note": [
        "Sales return credit note",
        "Credit note issued against damaged goods",
        "Credit adjustment invoice",
        "Customer return credit note",
        "Credit note for cancelled order"
    ],

    "Debit Note": [
        "Debit note for freight charges",
        "Debit note raised for additional tax",
        "Supplier debit adjustment",
        "Debit note against shortage",
        "Debit note for transport expenses"
    ],

    "GST Payment": [
        "GST payment challan",
        "GST liability payment",
        "Monthly GST tax payment",
        "GST deposited through bank",
        "GST payment for current month"
    ],

    "GST Refund": [
        "GST refund received",
        "Input GST refund",
        "GST refund from department",
        "Export GST refund",
        "Refund received under GST"
    ],

    "Reverse Charge": [
        "Legal service under reverse charge",
        "Advocate service payment",
        "GTA transport service",
        "Director remuneration",
        "Reverse charge professional service"
    ],

    "Exempt Supply": [
        "Healthcare exempt supply",
        "Educational service invoice",
        "Hospital treatment charges",
        "Agricultural produce sale",
        "School tuition fees"
    ]
}

records = []

for category, templates in categories.items():

    for _ in range(500):

        template = random.choice(templates)

        amount = random.randint(1000, 500000)

        if "{}" in template:

            if category in ["Export", "Import"]:
                value = random.choice(countries)

            elif category == "B2B":
                value = random.choice(companies)

            else:
                value = random.choice(companies)

            text = template.format(value)

        else:
            text = template

        invoice_text = (
            f"{text} Rs {amount}"
        )

        records.append(
            [invoice_text, category]
        )

df = pd.DataFrame(
    records,
    columns=[
        "Invoice_Text",
        "Category"
    ]
)

df = df.sample(
    frac=1,
    random_state=42
).reset_index(drop=True)

output_file = (
    "gst-classifier/datasets/gst_invoices_5000.csv"
)

df.to_csv(
    output_file,
    index=False
)

print("\nDataset Generated Successfully!")

print("\nFile :", output_file)

print("\nTotal Records :", len(df))

print("\nCategory Distribution:")
print(df["Category"].value_counts())

print("\nDataset Preview:")
print(df.head())
