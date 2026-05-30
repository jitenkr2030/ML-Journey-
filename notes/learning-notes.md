# My ML Learning Notes

## What I Learned

### Data Leakage

Using current close price indirectly leaked future information into the model.

This created fake perfect predictions.

---

### Time-Series Forecasting

Forecasting must always use:

Past → Future

Never future information.

---

### Evaluation Metrics

MAE:
Average prediction error.

RMSE:
Punishes large mistakes.

R²:
Measures how well patterns are explained.
