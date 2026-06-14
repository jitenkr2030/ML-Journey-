import pandas as pd
import random

print("\nGenerating GST Dataset - 2000 Records")

companies = [
    "TCS", "Infosys", "Wipro", "HCL",
    "Google", "Amazon", "Flipkart",
    "Reliance", "Tata Steel", "Adani",
    "Microsoft", "IBM", "Oracle",
    "Accenture", "Deloitte"
]

countries = [
    "USA",
    "UK",
    "Canada",
    "Germany",
    "Australia",
    "Singapore",
    "Japan"
]

records = []

categories = {

    "B2B": [
        "GST Invoice to {} Rs {}",
        "Wholesale Sale to {} Rs {}",
        "Corporate Invoice for {} Rs {}",
        "Tax Invoice issued to {} Rs {}"
    ],

    "B2C": [
        "Retail Sale Invoice Rs {}",
        "Customer Purchase Bill Rs {}",
        "Consumer Invoice Rs {}",
        "Cash Sale Bill Rs {}"
    ],

    "Export": [
        "Export Invoice to {} Rs {}",
        "International Sale to {} Rs {}",
        "Export Supply Invoice {} Rs {}",
        "LUT Export Invoice to {} Rs {}"
    ],

    "Import": [
        "Import Goods From {} Rs {}",
        "Overseas Supplier Invoice {} Rs {}",
        "Import Purchase Bill {} Rs {}",
        "Import Material Invoice {} Rs {}"
    ],

    "Credit Note": [
        "Credit Note Against Invoice Rs {}",
        "Customer Credit Note Rs {}",
        "Sales Return Credit Note Rs {}",
        "Credit Adjustment Note Rs {}"
    ],

    "Debit Note": [
        "Debit Note For Freight Rs {}",
        "Vendor Debit Note Rs {}",
        "Purchase Adjustment Debit Note Rs {}",
        "Debit Note For Short Supply Rs {}"
    ],

    "GST Payment": [
        "GST Challan Payment Rs {}",
        "GST Tax Payment Rs {}",
        "Monthly GST Deposit Rs {}",
        "GST Liability Payment Rs {}"
    ],

    "GST Refund": [
        "GST Refund Received Rs {}",
        "Input GST Refund Rs {}",
        "GST Claim Refund Rs {}",
        "Export GST Refund Rs {}"
    ],

    "Reverse Charge": [
        "Legal Service Under RCM Rs {}",
        "Advocate Invoice RCM Rs {}",
        "Reverse Charge GST Service Rs {}",
        "RCM Professional Fees Rs {}"
    ],

    "Exempt Supply": [
        "Healthcare Service Invoice Rs {}",
        "Education Service Invoice Rs {}",
        "Exempt Supply Bill Rs {}",
        "Medical Service Exempt Invoice Rs {}"
    ]
}

records_per_category = 200

for category, templates in categories.items():

    for i in range(records_per_category):

        template = random.choice(templates)

        amount = random.randint(
            1000,
            500000
        )

        company = random.choice(companies)

        country = random.choice(countries)

        placeholder_count = template.count("{}")

        if placeholder_count == 2:

            if category in ["Export", "Import"]:
                invoice_text = template.format(
                    country,
                    amount
                )
            else:
                invoice_text = template.format(
                    company,
                    amount
                )

        elif placeholder_count == 1:

            invoice_text = template.format(
                amount
            )

        else:

            invoice_text = template

        records.append([
            invoice_text,
            category
        ])

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
    "gst-classifier/datasets/gst_invoices_2000.csv"
)

df.to_csv(
    output_file,
    index=False
)

print("\nDataset Generated Successfully!")
print("File :", output_file)
print("Total Records :", len(df))

print("\nCategory Distribution:")
print(
    df["Category"].value_counts()
)
