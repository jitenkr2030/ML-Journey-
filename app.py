import yfinance as yf
import pandas as pd
import numpy as np

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression

from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score
)

# Download stock data
df = yf.download("RELIANCE.NS", period="1y")

# =========================
# FEATURE ENGINEERING
# =========================

# Use ONLY previous day information

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

# Target = Tomorrow Close
df['Tomorrow_Close'] = df['Close'].shift(-1)

# Remove empty rows
df.dropna(inplace=True)

# =========================
# FEATURES (X)
# =========================

X = df[[
    'Prev_Close',
    'Prev_Open',
    'Prev_High',
    'Prev_Low',
    'Prev_Volume',
    'Prev_MA5'
]]

# =========================
# TARGET (y)
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

# =========================
# MODEL
# =========================

model = LinearRegression()

# Train model
model.fit(X_train, y_train)

# =========================
# PREDICTIONS
# =========================

predictions = model.predict(X_test)

# =========================
# EVALUATION METRICS
# =========================

mae = mean_absolute_error(y_test, predictions)

mse = mean_squared_error(y_test, predictions)

rmse = np.sqrt(mse)

r2 = r2_score(y_test, predictions)

# =========================
# RESULTS
# =========================

print("\nModel Trained Successfully!")

print(f"\nMAE  : {mae}")

print(f"RMSE : {rmse}")

print(f"R²   : {r2}")

# Predictions table
results = pd.DataFrame({
    'Actual': y_test.values.ravel(),
    'Predicted': predictions.ravel()
})

print("\nPredictions:")

print(results.head())
