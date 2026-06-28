import numpy as np
from sklearn.ensemble import IsolationForest

# Pre-trained model (trained on synthetic normal distribution data at startup)
_model: IsolationForest = None


def _get_model() -> IsolationForest:
    global _model
    if _model is None:
        # Synthetic normal behaviour training data
        rng = np.random.RandomState(42)
        normal_data = np.column_stack([
            rng.uniform(0.6, 0.95, 300),   # distribution_ratio
            rng.uniform(0.5, 5.0,  300),   # txn_per_day
            rng.uniform(0,   2.0,  300),   # complaint_count (normalised /30)
            rng.uniform(0,  15.0,  300),   # mismatch_pct
        ])
        _model = IsolationForest(n_estimators=100, contamination=0.1, random_state=42)
        _model.fit(normal_data)
    return _model


def run_fraud_detection(features: dict) -> dict:
    """
    Inputs (dict):
        distribution_ratio  – stock_distributed / stock_received
        txn_per_day         – avg daily transactions over last 30 days
        complaint_count     – complaints in last 30 days
        mismatch_pct        – |received - distributed| / received * 100

    Returns:
        anomaly_score       – normalised 0-1 (higher = more anomalous)
        is_fraud_suspected  – bool
        reason_text         – human-readable explanation
    """
    model = _get_model()

    X = np.array([[
        features.get("distribution_ratio", 0.5),
        features.get("txn_per_day", 1.0),
        features.get("complaint_count", 0) / 30.0,
        features.get("mismatch_pct", 0),
    ]])

    raw_score   = model.decision_function(X)[0]   # negative = anomalous
    prediction  = model.predict(X)[0]             # -1 = anomaly, 1 = normal

    # Normalise to 0-1 (higher = worse)
    anomaly_score = float(np.clip(1 - (raw_score + 0.5), 0, 1))
    is_fraud      = prediction == -1

    reasons = []
    if features.get("distribution_ratio", 1) < 0.3:
        reasons.append("Very low stock distribution ratio (possible diversion)")
    if features.get("distribution_ratio", 0) > 0.98:
        reasons.append("Near-total stock distributed — unusually high velocity")
    if features.get("complaint_count", 0) > 5:
        reasons.append(f"High complaint count ({features['complaint_count']}) in last 30 days")
    if features.get("mismatch_pct", 0) > 20:
        reasons.append(f"Stock mismatch of {features['mismatch_pct']:.1f}% detected")
    if features.get("txn_per_day", 0) > 10:
        reasons.append(f"Unusually high transaction rate ({features['txn_per_day']:.1f}/day)")
    if not reasons:
        reasons.append("Statistical anomaly detected by Isolation Forest model")

    return {
        "anomaly_score": round(anomaly_score, 4),
        "is_fraud_suspected": bool(is_fraud),
        "reason_text": "; ".join(reasons) if is_fraud else "No significant anomaly detected",
    }
