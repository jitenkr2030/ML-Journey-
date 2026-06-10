import pandas as pd

from sklearn.model_selection import train_test_split

from sklearn.feature_extraction.text import TfidfVectorizer

from sklearn.naive_bayes import MultinomialNB

from sklearn.metrics import accuracy_score


print("\nFinancial Expense Classification - Day 5")

# ==================================
# DATASET
# ==================================

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

# ==================================
# FEATURES AND LABELS
# ==================================

X = df["Description"]

y = df["Category"]

# ==================================
# TRAIN / TEST SPLIT
# ==================================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.30,
    random_state=42
)

print("\nTraining Records :", len(X_train))
print("Testing Records  :", len(X_test))

# ==================================
# TF-IDF VECTORIZATION
# ==================================

print("\nConverting text into numbers using TF-IDF...")

vectorizer = TfidfVectorizer()

X_train_vector = vectorizer.fit_transform(X_train)

X_test_vector = vectorizer.transform(X_test)

print("Vectorization Completed!")

# ==================================
# MODEL TRAINING
# ==================================

print("\nTraining Naive Bayes Model...")

model = MultinomialNB()

model.fit(
    X_train_vector,
    y_train
)

# ==================================
# PREDICTIONS
# ==================================

predictions = model.predict(
    X_test_vector
)

# ==================================
# EVALUATION
# ==================================

accuracy = accuracy_score(
    y_test,
    predictions
)

print("\nModel Accuracy :", round(accuracy, 2))

# ==================================
# CUSTOM PREDICTIONS
# ==================================

sample_expenses = [

    "Uber Airport Ride",

    "Electricity Payment",

    "Salary Transfer",

    "Office Printer Purchase",

    "Client Lunch Meeting"
]

sample_vector = vectorizer.transform(
    sample_expenses
)

sample_predictions = model.predict(
    sample_vector
)

print("\nExpense Predictions")

for expense, category in zip(
    sample_expenses,
    sample_predictions
):

    print(
        f"{expense} --> {category}"
    )

print("\nDay 5 Completed Successfully!")
