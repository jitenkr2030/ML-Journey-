import yfinance as yf
import pandas as pd
import numpy as np

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor

from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score
)

# =========================
# DOWNLOAD STOCK DATA
# =========================

print("\nDownloading RELIANCE stock data...")

df = yf.download(
    "RELIANCE.NS",
    period="1y"
)

# =========================
# FEATURE ENGINEERING
# =========================

print("Creating features...")

# Previous day information

df['Prev_Close'] = df['Close'].shift(1)

df['Prev_Open'] = df['Open'].shift(1)

df['Prev_High'] = df['High'].shift(1)

df['Prev_Low'] = df['Low'].shift(1)

df['Prev_Volume'] = df['Volume'].shift(1)

# Previous 5-day moving average

df['Prev_MA5'] = (
    df['Close']
    .shift(1)
    .rolling(window=5)
    .mean()
)

# Tomorrow's close price

df['Tomorrow_Close'] = df['Close'].shift(-1)

# Remove empty rows

df.dropna(inplace=True)

# =========================
# FEATURES
# =========================

X = df[
    [
        'Prev_Close',
        'Prev_Open',
        'Prev_High',
        'Prev_Low',
        'Prev_Volume',
        'Prev_MA5'
    ]
]

# =========================
# TARGET
# =========================

y = df['Tomorrow_Close']

# =========================
# TRAIN / TEST SPLIT
# =========================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42
)

print("\nTraining Rows :", len(X_train))
print("Testing Rows  :", len(X_test))

# =========================
# MODEL COMPARISON
# =========================

models = {

    "Linear Regression": LinearRegression(),

    "Decision Tree": DecisionTreeRegressor(
        random_state=42
    ),

    "Random Forest": RandomForestRegressor(
        n_estimators=100,
        random_state=42
    )
}

# =========================
# TRAIN AND EVALUATE
# =========================

for name, model in models.items():

    print("\n" + "=" * 60)

    print(f"MODEL : {name}")

    print("=" * 60)

    # Train model

    model.fit(
        X_train,
        y_train
    )

    # Predictions

    predictions = model.predict(
        X_test
    )

    # Metrics

    mae = mean_absolute_error(
        y_test,
        predictions
    )

    mse = mean_squared_error(
        y_test,
        predictions
    )

    rmse = np.sqrt(
        mse
    )

    r2 = r2_score(
        y_test,
        predictions
    )

    # Results

    print(f"MAE  : {mae:.2f}")

    print(f"RMSE : {rmse:.2f}")

    print(f"R²   : {r2:.4f}")

    # Sample predictions

    results = pd.DataFrame({
        "Actual": y_test.values.ravel(),
        "Predicted": predictions.ravel()
    })

    print("\nSample Predictions:")

    print(results.head())

print("\nML Model Comparison Completed Successfully!")
