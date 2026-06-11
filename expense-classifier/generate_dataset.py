import pandas as pd

data = []

categories = {
    "Travel": [
        "Uber Ride","Ola Cab","Flight Ticket","Train Ticket",
        "Metro Card Recharge","Airport Taxi","Hotel Booking",
        "Business Travel Expense","Cab Fare","Taxi Bill",
        "Auto Rickshaw Fare","Railway Booking","Air India Ticket",
        "Indigo Flight Booking","Travel Reimbursement",
        "Corporate Taxi","Airport Pickup","Airport Drop",
        "Client Visit Travel","Business Flight Booking",
        "Local Travel Expense","Travel Advance",
        "Hotel Stay Expense","Outstation Travel",
        "Cab Booking Expense"
    ],

    "Utilities": [
        "Electricity Bill","Water Bill","Internet Bill",
        "Airtel Broadband","Jio Fiber Payment","BSNL Bill",
        "Office Electricity Payment","Utility Expense",
        "Power Bill","Internet Recharge",
        "WiFi Charges","Telephone Bill",
        "Mobile Bill","Data Connection Charges",
        "Electricity Charges","Office Water Charges",
        "Electric Meter Recharge","Fiber Internet Bill",
        "Broadband Renewal","Utility Service Charges",
        "Office Mobile Recharge","Landline Bill",
        "Network Charges","Data Pack Recharge",
        "Internet Service Provider Bill"
    ],

    "Payroll": [
        "Salary Payment","Employee Salary","Staff Salary",
        "Monthly Payroll","Salary Transfer",
        "Payroll Expense","Wages Payment",
        "Bonus Payment","HR Salary Transfer",
        "Employee Reimbursement","Payroll Processing",
        "Staff Wages","Salary Credit",
        "Payroll Settlement","Worker Salary",
        "Contractor Payment","Employee Bonus",
        "Festival Bonus","Salary Advance",
        "Payroll Adjustment","Attendance Incentive",
        "Overtime Payment","Staff Allowance",
        "Employee Benefits","HR Payroll Expense"
    ],

    "Office Expense": [
        "Amazon Office Supplies","Printer Purchase",
        "Laptop Purchase","Office Chair Purchase",
        "Office Desk Purchase","Stationery Purchase",
        "Office Equipment","Printer Ink Purchase",
        "Computer Accessories","Office Furniture",
        "Whiteboard Purchase","Office Supplies Order",
        "Keyboard Purchase","Mouse Purchase",
        "Office Maintenance","Monitor Purchase",
        "Scanner Purchase","UPS Purchase",
        "Office Cleaning Expense","Office Repair Expense",
        "Projector Purchase","Printer Repair",
        "Paper Purchase","Stapler Purchase",
        "Office Consumables"
    ],

    "Business Meeting": [
        "Restaurant Client Meeting",
        "Business Lunch",
        "Client Dinner",
        "Meeting Expense",
        "Conference Lunch",
        "Business Breakfast",
        "Customer Meeting Expense",
        "Sales Meeting Lunch",
        "Project Discussion Dinner",
        "Corporate Lunch",
        "Management Meeting",
        "Board Meeting Lunch",
        "Executive Dinner",
        "Investor Meeting",
        "Client Coffee Meeting",
        "Business Networking Event",
        "Vendor Meeting Lunch",
        "Sales Presentation Lunch",
        "Project Review Meeting",
        "Business Conference Dinner"
    ],

    "Marketing": [
        "Google Ads Payment",
        "Facebook Ads Payment",
        "LinkedIn Ads",
        "Marketing Campaign Expense",
        "Promotional Expense",
        "SEO Service Payment",
        "Digital Marketing Charges",
        "Advertisement Expense",
        "Social Media Marketing",
        "Marketing Agency Payment",
        "Google Search Ads",
        "Instagram Ads",
        "YouTube Ads",
        "Email Marketing Service",
        "Marketing Consultant Fee",
        "Lead Generation Expense",
        "Brand Promotion Expense",
        "Influencer Marketing",
        "Online Advertising",
        "Campaign Management Fee"
    ],

    "Rent": [
        "Office Rent",
        "Monthly Rent",
        "Building Rent",
        "Workspace Rent",
        "Commercial Rent",
        "Office Lease Payment",
        "Rent Transfer",
        "Rental Expense",
        "Property Rent",
        "Office Space Rent",
        "Warehouse Rent",
        "Storage Rent",
        "Shop Rent",
        "Office Rental Charges",
        "Premises Rent"
    ],

    "Software": [
        "ChatGPT Subscription",
        "GitHub Subscription",
        "Zoom Subscription",
        "Microsoft 365",
        "Canva Subscription",
        "Adobe Subscription",
        "Software License Fee",
        "Cloud Hosting Fee",
        "AWS Subscription",
        "Google Workspace",
        "OpenAI API Charges",
        "Cursor Subscription",
        "Claude Subscription",
        "Figma Subscription",
        "Notion Subscription",
        "DigitalOcean Hosting",
        "VPS Hosting Charges",
        "Domain Renewal",
        "SSL Certificate Renewal",
        "Software Maintenance Fee"
    ],

    "GST": [
        "GST Payment",
        "CGST Payment",
        "SGST Payment",
        "IGST Payment",
        "GST Challan",
        "GST Liability Payment",
        "GST Return Filing",
        "Tax Payment GST",
        "GST Expense",
        "GST Settlement",
        "GST Interest Payment",
        "GST Late Fee",
        "GST Demand Payment",
        "GST Adjustment",
        "GST Refund Processing",
        "GST Filing Charges",
        "GST Portal Payment",
        "GST Penalty",
        "GST Reconciliation Expense",
        "GST Assessment Payment"
    ],

    "Bank Charges": [
        "Bank Charges",
        "ATM Charges",
        "Cheque Bounce Charges",
        "Processing Charges",
        "Account Maintenance Charges",
        "RTGS Charges",
        "NEFT Charges",
        "Bank Service Fee",
        "Transaction Charges",
        "Bank Penalty",
        "Bank SMS Charges",
        "Debit Card Annual Fee",
        "Credit Card Charges",
        "Bank Processing Fee",
        "Account Statement Charges",
        "Cash Deposit Charges",
        "Cheque Book Charges",
        "Bank Documentation Charges",
        "Online Banking Charges",
        "Bank Transaction Fee"
    ],

    "Vendor Payment": [
        "Vendor Payment",
        "Supplier Payment",
        "Raw Material Purchase",
        "Vendor Settlement",
        "Purchase Invoice Payment",
        "Contractor Invoice Payment",
        "Supplier Transfer",
        "Vendor Advance",
        "Vendor Bill Payment",
        "Material Purchase Expense"
    ],

    "Insurance": [
        "Health Insurance Premium",
        "Vehicle Insurance",
        "Office Insurance",
        "Group Insurance Policy",
        "Professional Liability Insurance",
        "Fire Insurance Premium",
        "Business Insurance",
        "Employee Insurance",
        "Insurance Renewal",
        "Insurance Claim Charges"
    ]
}

for category, descriptions in categories.items():
    for description in descriptions:
        data.append([description, category])

df = pd.DataFrame(
    data,
    columns=["Description", "Category"]
)

df.to_csv(
    "financial_expenses_260.csv",
    index=False
)

print(df.head())
print("\nTotal Records:", len(df))
print("\nCSV Generated Successfully!")
