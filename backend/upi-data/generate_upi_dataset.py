import csv
import random
import os

random.seed(42)

# UPI Transaction Types
UPI_TYPES = [
    "P2P", "P2M", "Merchant Payment", "Bill Payment",
    "Mobile Recharge", "EMI Payment", "Subscription",
    "Insurance Premium", "Rent Payment", "Salary Transfer"
]

# UPI Apps
UPI_APPS = ["GPay", "PhonePe", "Paytm", "BHIM", "AmazonPay", "Cred", "Mobikwik"]

# UPI ID Patterns
UPI_IDS = [
    "user@paytm", "user@ybl", "user@okhdfcbank", "user@oksbi",
    "merchant@razorpay", "merchant@payu", "merchant@ccavenue",
    "user@apl", "user@ibl", "user@axl", "user@federal",
    "abc123@paytm", "xyz456@ybl", "shop@okicici", "store@okaxis",
    "pay@oksbi", "bill@paytm", "rent@upi", "salary@bank"
]

# UPI Narration Patterns (as seen in bank statements)
NARRATION_PATTERNS = [
    "UPI/DR/{utr}/{payer}/{type}",
    "UPI/CR/{utr}/{payee}/{type}",
    "UPI/{app}/{utr}/{name}/{type}",
    "IMPS/{utr}/{name}/{type}",
    "NEFT/{utr}/{name}/{type}",
    "UPI P2P {name} {utr}",
    "UPI P2M {merchant} {utr}",
    "PAYMENT TO {merchant} VIA {app}",
    "RECEIVED FROM {payer} VIA {app}",
    "{app} UPI TRANSFER {name} REF:{utr}",
    "BILL PAYMENT {bill_type} REF:{utr}",
    "SUBSCRIPTION {service} REF:{utr}",
    "EMI PAYMENT {bank} REF:{utr}",
    "RECHARGE {operator} REF:{utr}",
    "INSURANCE PREMIUM {company} REF:{utr}",
]

# Names for transactions
NAMES = [
    "RAHUL SHARMA", "PRIYA PATEL", "AMIT KUMAR", "SNEHA SINGH",
    "VIKAS GUPTA", "ANITA DEVI", "RAJESH YADAV", "MEERA JOSHI",
    "SUNIL VERMA", "KAVITA REDDY", "ARUN NAIR", "DEEPA KAPOOR",
    "MOHAN LAL", "GEETA AGRAWAL", "SURESH PANDIT", "LATA MISHRA",
    "RAVI TEJA", "NEHA CHOPRA", "KIRAN SINGH", "ARUN KUMAR",
]

MERCHANTS = [
    "AMAZON", "FLIPKART", "SWIGGY", "ZOMATO", "BIGBASKET",
    "RELIANCE RETAIL", "DMART", "CROMA", "TATACLIQ",
    "NETFLIX", "SPOTIFY", "HOTSTAR", "PRIME VIDEO",
    "AIRTEL", "JIO", "VODAFONE", "BSNL",
    "HDFC BANK", "ICICI BANK", "SBI", "AXIS BANK",
    "BAJAJ FINSERV", "LIC", "STAR HEALTH", "HDFC LIFE",
]

BILL_TYPES = ["ELECTRICITY", "GAS", "WATER", "INTERNET", "DTH", "LANDLINE", "MOBILE"]
SERVICES = ["NETFLIX", "SPOTIFY", "AMAZON PRIME", "GOOGLE ONE", "APPLE ICLOUD"]
OPERATORS = ["AIRTEL", "JIO", "VI", "BSNL"]
COMPANIES = ["LIC", "SBI LIFE", "ICICI PRUDENTIAL", "STAR HEALTH", "BAJAJ ALLIANZ"]

# Status values
STATUSES = ["Matched", "Unmatched", "UPI Failed", "UPI Reversed", "Partial Match", "Duplicate", "Pending Settlement"]


def generate_utr():
    return f"{random.randint(10**11, 10**12-1)}"


def generate_upi_id():
    return random.choice(UPI_IDS)


def generate_narration():
    pattern = random.choice(NARRATION_PATTERNS)
    narration = pattern.replace("{utr}", generate_utr())
    narration = narration.replace("{payer}", random.choice(NAMES))
    narration = narration.replace("{payee}", random.choice(NAMES))
    narration = narration.replace("{name}", random.choice(NAMES))
    narration = narration.replace("{merchant}", random.choice(MERCHANTS))
    narration = narration.replace("{app}", random.choice(UPI_APPS))
    narration = narration.replace("{type}", random.choice(UPI_TYPES))
    narration = narration.replace("{bill_type}", random.choice(BILL_TYPES))
    narration = narration.replace("{service}", random.choice(SERVICES))
    narration = narration.replace("{operator}", random.choice(OPERATORS))
    narration = narration.replace("{company}", random.choice(COMPANIES))
    narration = narration.replace("{bank}", random.choice(["HDFC", "ICICI", "SBI", "AXIS", "KOTAK"]))
    return narration


def generate_amount():
    amounts = [100, 200, 250, 500, 750, 1000, 1200, 1500, 2000, 2500, 3000,
               5000, 7500, 10000, 15000, 20000, 25000, 50000, 75000, 100000,
               150, 350, 450, 550, 650, 850, 950, 1100, 1300, 1750, 2250,
               499, 999, 1499, 1999, 2999, 3999, 4999, 9999, 14999, 19999]
    return random.choice(amounts)


def generate_reference():
    return f"REF{random.randint(10000, 99999)}"


def generate_cheque():
    return f"CHQ{random.randint(1000, 9999)}" if random.random() > 0.7 else ""


def generate_date():
    year = 2026
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    return f"{year}-{month:02d}-{day:02d}"


def generate_row(status):
    book_narration = generate_narration()
    bank_narration = book_narration
    book_amount = generate_amount()
    bank_amount = book_amount
    book_date = generate_date()
    bank_date = book_date
    book_ref = generate_reference()
    bank_ref = book_ref
    book_chq = generate_cheque()
    bank_chq = book_chq

    if status == "Matched":
        pass  # Everything matches

    elif status == "Unmatched":
        bank_narration = ""
        bank_amount = 0
        bank_ref = ""
        bank_chq = ""

    elif status == "UPI Failed":
        bank_amount = 0
        bank_narration = f"UPI FAILED {generate_utr()}"

    elif status == "UPI Reversed":
        bank_amount = -book_amount
        bank_narration = f"UPI REVERSAL {generate_utr()}"

    elif status == "Partial Match":
        diff = random.choice([0.01, 0.05, 0.10, 0.50, 1.00, 5.00])
        bank_amount = book_amount + random.choice([-diff, diff])
        bank_date = book_date

    elif status == "Duplicate":
        pass  # Will be handled in dedup logic

    elif status == "Pending Settlement":
        bank_narration = f"UPI PENDING SETTLEMENT {generate_utr()}"
        bank_date = generate_date()

    # Randomly vary some fields for realism
    if random.random() > 0.8:
        bank_ref = generate_reference()  # Different ref
    if random.random() > 0.85:
        bank_date = generate_date()  # Different date (1 day off)

    return {
        "Book_Description": book_narration,
        "Bank_Description": bank_narration,
        "Book_Amount": book_amount,
        "Bank_Amount": bank_amount,
        "Book_Date": book_date,
        "Bank_Date": bank_date,
        "Book_Reference": book_ref,
        "Bank_Reference": bank_ref,
        "Book_Cheque": book_chq,
        "Bank_Cheque": bank_chq,
        "UPI_ID": generate_upi_id(),
        "UPI_Type": random.choice(UPI_TYPES),
        "UPI_App": random.choice(UPI_APPS),
        "Status": status,
    }


# Generate 5000 records
rows = []
status_weights = {
    "Matched": 0.40,
    "Unmatched": 0.15,
    "UPI Failed": 0.10,
    "UPI Reversed": 0.08,
    "Partial Match": 0.12,
    "Duplicate": 0.05,
    "Pending Settlement": 0.10,
}

for i in range(5000):
    status = random.choices(list(status_weights.keys()), list(status_weights.values()))[0]
    rows.append(generate_row(status))

# Save
output_path = os.path.join(os.path.dirname(__file__), "upi_reconciliation_5000.csv")
fieldnames = rows[0].keys()
with open(output_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"Generated {len(rows)} UPI reconciliation records")
print(f"Saved to: {output_path}")

# Print distribution
from collections import Counter
dist = Counter(r["Status"] for r in rows)
for status, count in dist.most_common():
    print(f"  {status}: {count} ({count/len(rows)*100:.1f}%)")
