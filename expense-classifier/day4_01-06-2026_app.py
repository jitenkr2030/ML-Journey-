import pandas as pd

from sklearn.model_selection import train_test_split

from sklearn.feature_extraction.text import CountVectorizer

from sklearn.naive_bayes import MultinomialNB

from sklearn.metrics import accuracy_score


# =========================
# DATASET
# =========================

data = {

    "Description": [

        "Uber Ride",
        "Ola Cab",
        "Flight Ticket",
        "Train Ticket",

        "Electricity Bill",
        "Water Bill",
        "Internet Bill",

        "Salary Payment",
        "Employee Salary",

        "Amazon Office Supplies",
        "Printer Purchase",
        "Laptop Purchase",

        "Restaurant Client Meeting",
        "Business Lunch"
    ],

    "Category": [

        "Travel",
        "Travel",
        "Travel",
        "Travel",

        "Utilities",
        "Utilities",
        "Utilities",

        "Payroll",
        "Payroll",

        "Office Expense",
        "Office Expense",
        "Office Expense",

        "Business Meeting",
        "Business Meeting"
    ]
}

df = pd.DataFrame(data)

print("\nDataset:")
print(df)

# =========================
# FEATURES AND LABELS
# =========================

X = df["Description"]

y = df["Category"]

# =========================
# TEXT TO NUMBERS
# =========================

vectorizer = CountVectorizer()

X_vectorized = vectorizer.fit_transform(X)

# =========================
# TRAIN TEST SPLIT
# =========================

X_train, X_test, y_train, y_test = train_test_split(
    X_vectorized,
    y,
    test_size=0.2,
    random_state=42
)

# =========================
# MODEL
# =========================

model = MultinomialNB()

print("\nTraining Model...")

model.fit(X_train, y_train)

# =========================
# PREDICTIONS
# =========================

predictions = model.predict(X_test)

# =========================
# ACCURACY
# =========================

accuracy = accuracy_score(
    y_test,
    predictions
)

print("\nAccuracy :", accuracy)

# =========================
# NEW EXPENSE PREDICTION
# =========================

new_expenses = [

    "Uber Airport Ride",
    "Electricity Payment",
    "Salary Transfer",
    "Laptop Purchase"
]

new_data = vectorizer.transform(
    new_expenses
)

results = model.predict(
    new_data
)

print("\nExpense Predictions")

for expense, category in zip(
        new_expenses,
        results):

    print(
        f"{expense} --> {category}"
    )

print("\nDay 4 Completed Successfully!")
