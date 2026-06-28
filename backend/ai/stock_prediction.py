from datetime import datetime
from typing import List, Dict
import numpy as np
from sklearn.linear_model import LinearRegression


def predict_stock_demand(
    transactions: List[Dict],
    beneficiary_count: int,
    festival_month: bool = False,
) -> float:
    """
    Predict next-month demand using Linear Regression on past 6 months.

    Args:
        transactions    – list of {"date": datetime, "qty": float}
        beneficiary_count – number of registered beneficiaries at this shop
        festival_month  – whether next month is a festival month

    Returns:
        predicted_demand_kg (float)
    """
    if not transactions:
        # Fallback: 5 kg per beneficiary per month
        base = beneficiary_count * 5.0
        return round(base * (1.1 if festival_month else 1.0), 2)

    # Aggregate by month index (0 = oldest, N = most recent)
    monthly: Dict[str, float] = {}
    for t in transactions:
        key = t["date"].strftime("%Y-%m")
        monthly[key] = monthly.get(key, 0) + t["qty"]

    monthly_values = list(monthly.values())

    if len(monthly_values) < 2:
        avg = sum(monthly_values) / len(monthly_values)
        return round(avg * (1.1 if festival_month else 1.0), 2)

    X = np.arange(len(monthly_values)).reshape(-1, 1)
    y = np.array(monthly_values)

    model = LinearRegression()
    model.fit(X, y)

    next_idx = np.array([[len(monthly_values)]])
    predicted = float(model.predict(next_idx)[0])

    # Festival month boost
    if festival_month:
        predicted *= 1.15

    # Clamp: can't be negative, cap at 10x average
    avg = float(np.mean(y))
    predicted = max(predicted, avg * 0.5)
    predicted = min(predicted, avg * 3.0)

    return round(predicted, 2)
