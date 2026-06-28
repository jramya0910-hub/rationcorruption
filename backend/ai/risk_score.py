def calculate_risk_score(
    fraud_score: float,
    complaint_count: int,
    mismatch_pct: float,
    txn_per_day: float,
) -> dict:
    """
    risk_score = (
        0.35 * fraud_anomaly_score +
        0.25 * complaint_rate_score +
        0.25 * stock_mismatch_score +
        0.15 * transaction_velocity_score
    ) * 100

    Returns:
        risk_score  – float 0-100
        risk_level  – "LOW" | "MEDIUM" | "HIGH"
    """
    # Normalise each component to 0-1
    fraud_component       = min(fraud_score, 1.0)
    complaint_component   = min(complaint_count / 10.0, 1.0)   # caps at 10 complaints
    mismatch_component    = min(mismatch_pct  / 50.0, 1.0)     # caps at 50% mismatch
    velocity_component    = min(txn_per_day   / 20.0, 1.0)     # caps at 20 txns/day

    risk_score = (
        0.35 * fraud_component +
        0.25 * complaint_component +
        0.25 * mismatch_component +
        0.15 * velocity_component
    ) * 100

    risk_score = round(risk_score, 2)

    if risk_score <= 40:
        risk_level = "LOW"
    elif risk_score <= 70:
        risk_level = "MEDIUM"
    else:
        risk_level = "HIGH"

    return {"risk_score": risk_score, "risk_level": risk_level}
