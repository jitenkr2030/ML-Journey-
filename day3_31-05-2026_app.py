import yfinance as yf
import pandas as pd
import numpy as np
import joblib
import os

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor

from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score
)

# =========================
# DOWNLOAD DATA
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

df['Prev_Close'] = df['Close'].shift(1)
df['Prev_Open'] = df['Open'].shift(1)
df['Prev_High'] = df['High'].shift(1)
df['Prev_Low'] = df['Low'].shift(1)
df['Prev_Volume'] = df['Volume'].shift(1)

df['Prev_MA5'] = (
    df['Close']
    .shift(1)
    .rolling(window=5)
    .mean()
)

df['Tomorrow_Close'] = df['Close'].shift(-1)

df.dropna(inplace=True)

# =========================
# FEATURES & TARGET
# =========================

feature_columns = [
    'Prev_Close',
    'Prev_Open',
    'Prev_High',
    'Prev_Low',
    'Prev_Volume',
    'Prev_MA5'
]

X = df[feature_columns]

y = df['Tomorrow_Close']

# =========================
# TRAIN TEST SPLIT
# =========================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42
)

# =========================
# RANDOM FOREST MODEL
# =========================

print("\nTraining Random Forest Model...")

model = RandomForestRegressor(
    n_estimators=100,
    random_state=42
)

model.fit(
    X_train,
    y_train
)

# =========================
# PREDICTIONS
# =========================

predictions = model.predict(X_test)

# =========================
# EVALUATION
# =========================

mae = mean_absolute_error(
    y_test,
    predictions
)

mse = mean_squared_error(
    y_test,
    predictions
)

rmse = np.sqrt(mse)

r2 = r2_score(
    y_test,
    predictions
)

print("\nModel Evaluation")

print(f"MAE  : {mae:.2f}")
print(f"RMSE : {rmse:.2f}")
print(f"R²   : {r2:.4f}")

# =========================
# FEATURE IMPORTANCE
# =========================

print("\nFeature Importance")

importance_df = pd.DataFrame({
    "Feature": feature_columns,
    "Importance": model.feature_importances_
})

importance_df = importance_df.sort_values(
    by="Importance",
    ascending=False
)

print(importance_df)

# =========================
# SAVE MODEL
# =========================

os.makedirs(
    "models",
    exist_ok=True
)

joblib.dump(
    model,
    "models/reliance_rf_model.pkl"
)

print(
    "\nModel saved successfully!"
)

# =========================
# LOAD MODEL
# =========================

loaded_model = joblib.load(
    "models/reliance_rf_model.pkl"
)

print(
    "Model loaded successfully!"
)

# =========================
# MANUAL PREDICTION
# =========================

latest_row = X.tail(1)

prediction = loaded_model.predict(
    latest_row
)

print(
    "\nNext Day Predicted Close Price:"
)

print(
    prediction[0]
)

# =========================
# SAMPLE PREDICTIONS
# =========================

results = pd.DataFrame({
    "Actual": y_test.values.ravel(),
    "Predicted": predictions.ravel()
})

print("\nSample Predictions")

print(results.head())

print(
    "\nDay 3 Completed Successfully!"
)
