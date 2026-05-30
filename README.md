# Stock Price Prediction ML Journey

This is my beginner machine learning project using Python, Conda, and Termux.

## Project Goal

Predict future stock closing prices using historical stock market data.

---

## Technologies Used

- Python
- Conda
- Pandas
- NumPy
- Scikit-learn
- yFinance

---

## ML Concepts Learned

- Data Collection
- Feature Engineering
- Linear Regression
- Train/Test Split
- MAE
- RMSE
- R² Score
- Data Leakage
- Time-Series Forecasting

---

## Features Used

- Previous Close
- Previous Open
- Previous High
- Previous Low
- Previous Volume
- Previous MA5

---

## Model Performance

Example Metrics:

- MAE: ~16
- RMSE: ~22
- R²: ~0.88

---

## Important Learning

Initially, the model showed perfect predictions because of data leakage.

After fixing temporal alignment and using only past information, the model became more realistic.

This project helped me understand:

- Real forecasting
- Temporal alignment
- Feature engineering
- Evaluation metrics
- Practical ML debugging

---

## Future Improvements

- Random Forest
- LSTM
- More indicators
- Real-time prediction
- Deployment with FastAPI

---

## Run Project

```bash
conda activate ml
python app.py
```

---

## Author

Jitender Kumar
