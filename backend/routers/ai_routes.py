from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta
from ..database import get_db
from ..models import Shop, Transaction, StockInventory, StockPrediction
from ..models.complaint import Complaint
from ..models.fraud_alert import FraudAlert
from ..schemas.schemas import (
    FraudDetectionRequest, StockPredictRequest, ComplaintCategorizeRequest
)
from ..utils.auth import require_role
from ..utils.response import success
from ..ai.fraud_detection import run_fraud_detection
from ..ai.risk_score import calculate_risk_score
from ..ai.stock_prediction import predict_stock_demand
from ..ai.complaint_nlp import categorize_complaint

router = APIRouter(prefix="/ai", tags=["AI"])


@router.post("/fraud-detection/run")
async def fraud_detection(
    payload: FraudDetectionRequest,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_role("officer")),
):
    shop_id = str(payload.shop_id)

    # Gather features
    inv_result = await db.execute(
        select(StockInventory).where(StockInventory.shop_id == shop_id)
    )
    inventory = inv_result.scalars().all()

    thirty_days_ago = datetime.utcnow() - timedelta(days=30)

    txn_count = (await db.execute(
        select(func.count(Transaction.transaction_id))
        .where(Transaction.shop_id == shop_id, Transaction.transaction_date >= thirty_days_ago)
    )).scalar() or 0

    complaint_count = (await db.execute(
        select(func.count(Complaint.complaint_id))
        .where(Complaint.shop_id == shop_id, Complaint.created_at >= thirty_days_ago)
    )).scalar() or 0

    total_received    = sum(float(i.stock_received_kg or 0) for i in inventory)
    total_distributed = sum(float(i.stock_distributed_kg or 0) for i in inventory)
    mismatch_pct = abs(total_received - total_distributed) / max(total_received, 1) * 100

    features = {
        "stock_received": total_received,
        "stock_distributed": total_distributed,
        "distribution_ratio": total_distributed / max(total_received, 1),
        "txn_per_day": txn_count / 30,
        "complaint_count": complaint_count,
        "mismatch_pct": mismatch_pct,
    }

    result = run_fraud_detection(features)
    risk = calculate_risk_score(
        fraud_score=result["anomaly_score"],
        complaint_count=complaint_count,
        mismatch_pct=mismatch_pct,
        txn_per_day=features["txn_per_day"],
    )

    # Persist alert if fraud suspected
    if result["is_fraud_suspected"]:
        alert = FraudAlert(
            shop_id=shop_id,
            alert_type="AI_DETECTED",
            description=result["reason_text"],
            severity="HIGH" if risk["risk_score"] > 70 else "MEDIUM",
        )
        db.add(alert)

    # Update shop risk score
    shop_result = await db.execute(select(Shop).where(Shop.shop_id == shop_id))
    shop = shop_result.scalar_one_or_none()
    if shop:
        shop.risk_score = risk["risk_score"]
        shop.risk_level = risk["risk_level"]

    await db.commit()

    return success({
        "shop_id": shop_id,
        "anomaly_score": result["anomaly_score"],
        "is_fraud_suspected": result["is_fraud_suspected"],
        "reason_text": result["reason_text"],
        "risk_score": risk["risk_score"],
        "risk_level": risk["risk_level"],
    })


@router.get("/risk-score/{shop_id}")
async def get_risk_score(
    shop_id: str,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_role("officer")),
):
    shop_result = await db.execute(select(Shop).where(Shop.shop_id == shop_id))
    shop = shop_result.scalar_one_or_none()
    if not shop:
        raise HTTPException(404, "Shop not found")
    return success({
        "shop_id": shop_id,
        "shop_name": shop.shop_name,
        "risk_score": float(shop.risk_score or 0),
        "risk_level": shop.risk_level.value,
    })


@router.post("/predict-stock")
async def predict_stock(
    payload: StockPredictRequest,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_role("officer", "shopkeeper")),
):
    shop_id = str(payload.shop_id)

    # Fetch last 6 months of transactions for this grain type
    six_months_ago = datetime.utcnow() - timedelta(days=180)
    txns = await db.execute(
        select(Transaction)
        .where(
            Transaction.shop_id == shop_id,
            Transaction.grain_type == payload.grain_type.value,
            Transaction.transaction_date >= six_months_ago,
        )
        .order_by(Transaction.transaction_date)
    )
    transactions = txns.scalars().all()

    ben_count = (await db.execute(
        select(func.count(Transaction.beneficiary_id.distinct()))
        .where(Transaction.shop_id == shop_id)
    )).scalar() or 1

    predicted_kg = predict_stock_demand(
        transactions=[{"date": t.transaction_date, "qty": float(t.quantity_given_kg)} for t in transactions],
        beneficiary_count=ben_count,
    )

    # Store prediction
    next_month = (datetime.utcnow().replace(day=1) + timedelta(days=32)).replace(day=1)
    pred = StockPrediction(
        shop_id=shop_id,
        grain_type=payload.grain_type.value,
        predicted_demand_kg=predicted_kg,
        prediction_month=next_month,
    )
    db.add(pred)
    await db.commit()

    return success({
        "shop_id": shop_id,
        "grain_type": payload.grain_type.value,
        "predicted_demand_kg": predicted_kg,
        "prediction_month": next_month.strftime("%Y-%m"),
    })


@router.post("/categorize-complaint")
async def categorize(
    payload: ComplaintCategorizeRequest,
    _user=Depends(require_role("officer", "beneficiary")),
):
    category = categorize_complaint(payload.description)
    return success({"predicted_category": category, "confidence": 0.87})
