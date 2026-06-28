import io
import csv
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from datetime import datetime
from ..database import get_db
from ..models import Shop, Beneficiary, Transaction, StockInventory, StockPrediction
from ..models.complaint import Complaint, ComplaintStatus
from ..models.fraud_alert import FraudAlert
from ..schemas.schemas import ComplaintResolveRequest
from ..utils.auth import require_role
from ..utils.response import success

router = APIRouter(prefix="/officer", tags=["Officer"])


@router.get("/dashboard")
async def get_dashboard(
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_role("officer")),
):
    total_shops = (await db.execute(func.count(Shop.shop_id).select())).scalar()
    total_bens  = (await db.execute(func.count(Beneficiary.beneficiary_id).select())).scalar()
    active_alerts = (await db.execute(
        select(func.count(FraudAlert.alert_id)).where(FraudAlert.is_reviewed == False)
    )).scalar()
    open_complaints = (await db.execute(
        select(func.count(Complaint.complaint_id)).where(Complaint.status == ComplaintStatus.OPEN)
    )).scalar()
    high_risk = (await db.execute(
        select(func.count(Shop.shop_id)).where(Shop.risk_level == "HIGH")
    )).scalar()

    # Bar chart data: distributed per shop
    shops_result = await db.execute(select(Shop))
    shops = shops_result.scalars().all()

    bar_data = []
    for shop in shops:
        inv_result = await db.execute(
            select(func.coalesce(func.sum(StockInventory.stock_distributed_kg), 0))
            .where(StockInventory.shop_id == shop.shop_id)
        )
        distributed = float(inv_result.scalar() or 0)
        bar_data.append({"shop_name": shop.shop_name, "distributed_kg": distributed})

    # Monthly trend (last 6 months)
    monthly = await db.execute(
        select(
            func.date_trunc("month", Transaction.transaction_date).label("month"),
            func.sum(Transaction.quantity_given_kg).label("total"),
        )
        .group_by("month")
        .order_by("month")
        .limit(6)
    )
    trend = [{"month": str(r.month)[:7], "total_kg": float(r.total or 0)} for r in monthly]

    # Complaint breakdown
    comp_result = await db.execute(
        select(Complaint.complaint_type, func.count(Complaint.complaint_id))
        .group_by(Complaint.complaint_type)
    )
    complaint_breakdown = [{"type": r[0].value, "count": r[1]} for r in comp_result.all()]

    return success({
        "summary": {
            "total_shops": total_shops,
            "total_beneficiaries": total_bens,
            "active_alerts": active_alerts,
            "open_complaints": open_complaints,
            "high_risk_shops": high_risk,
        },
        "bar_chart": bar_data,
        "monthly_trend": trend,
        "complaint_breakdown": complaint_breakdown,
    })


@router.get("/alerts")
async def get_alerts(
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_role("officer")),
):
    result = await db.execute(
        select(FraudAlert, Shop)
        .join(Shop, FraudAlert.shop_id == Shop.shop_id)
        .order_by(FraudAlert.created_at.desc())
    )
    rows = result.all()
    data = [
        {
            "alert_id": str(a.alert_id),
            "shop_name": s.shop_name,
            "shop_id": str(a.shop_id),
            "alert_type": a.alert_type,
            "description": a.description,
            "severity": a.severity.value,
            "is_reviewed": a.is_reviewed,
            "created_at": a.created_at.isoformat(),
        }
        for a, s in rows
    ]
    return success({"alerts": data})


@router.get("/shops/risk")
async def get_risk_shops(
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_role("officer")),
):
    result = await db.execute(
        select(Shop).order_by(Shop.risk_score.desc())
    )
    shops = result.scalars().all()
    data = [
        {
            "shop_id": str(s.shop_id),
            "shop_name": s.shop_name,
            "owner_name": s.owner_name,
            "district": s.district,
            "risk_score": float(s.risk_score or 0),
            "risk_level": s.risk_level.value,
        }
        for s in shops
    ]
    return success({"shops": data})


@router.get("/complaints")
async def get_all_complaints(
    status: str = Query(None),
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_role("officer")),
):
    query = (
        select(Complaint, Beneficiary, Shop)
        .join(Beneficiary, Complaint.beneficiary_id == Beneficiary.beneficiary_id)
        .join(Shop, Complaint.shop_id == Shop.shop_id)
        .order_by(Complaint.created_at.desc())
    )
    if status:
        query = query.where(Complaint.status == status.upper())

    result = await db.execute(query)
    rows = result.all()
    data = [
        {
            "complaint_id": str(c.complaint_id),
            "beneficiary_name": b.name,
            "shop_name": s.shop_name,
            "complaint_type": c.complaint_type.value,
            "description": c.description,
            "status": c.status.value,
            "ai_category": c.ai_category,
            "created_at": c.created_at.isoformat(),
            "resolved_at": c.resolved_at.isoformat() if c.resolved_at else None,
        }
        for c, b, s in rows
    ]
    return success({"complaints": data})


@router.post("/complaints/resolve")
async def resolve_complaint(
    payload: ComplaintResolveRequest,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_role("officer")),
):
    result = await db.execute(
        select(Complaint).where(Complaint.complaint_id == str(payload.complaint_id))
    )
    complaint = result.scalar_one_or_none()
    if not complaint:
        raise HTTPException(404, "Complaint not found")
    complaint.status = ComplaintStatus.RESOLVED
    complaint.resolved_at = datetime.utcnow()
    await db.commit()
    return success({}, "Complaint resolved")


@router.get("/predictions")
async def get_predictions(
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_role("officer")),
):
    result = await db.execute(
        select(StockPrediction, Shop)
        .join(Shop, StockPrediction.shop_id == Shop.shop_id)
        .order_by(StockPrediction.prediction_month.desc())
    )
    rows = result.all()
    data = [
        {
            "prediction_id": str(p.prediction_id),
            "shop_name": s.shop_name,
            "grain_type": p.grain_type.value,
            "predicted_demand_kg": float(p.predicted_demand_kg or 0),
            "prediction_month": p.prediction_month.isoformat() if p.prediction_month else None,
        }
        for p, s in rows
    ]
    return success({"predictions": data})


@router.get("/report/export")
async def export_report(
    format: str = Query("csv", regex="^(csv|pdf)$"),
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_role("officer")),
):
    # Fetch shop risk data
    result = await db.execute(select(Shop).order_by(Shop.risk_score.desc()))
    shops = result.scalars().all()

    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Shop Name", "Owner", "District", "Risk Score", "Risk Level"])
        for s in shops:
            writer.writerow([s.shop_name, s.owner_name, s.district, float(s.risk_score or 0), s.risk_level.value])
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=shop_risk_report.csv"},
        )
    else:
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
            from reportlab.lib import colors
            from reportlab.lib.styles import getSampleStyleSheet

            buf = io.BytesIO()
            doc = SimpleDocTemplate(buf, pagesize=letter)
            styles = getSampleStyleSheet()
            elements = [Paragraph("Smart Ration Guardian — Shop Risk Report", styles["Title"])]
            table_data = [["Shop Name", "Owner", "District", "Risk Score", "Risk Level"]]
            for s in shops:
                table_data.append([s.shop_name, s.owner_name, s.district, str(float(s.risk_score or 0)), s.risk_level.value])
            t = Table(table_data)
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
                ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
                ("GRID",       (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            elements.append(t)
            doc.build(elements)
            buf.seek(0)
            return StreamingResponse(
                buf,
                media_type="application/pdf",
                headers={"Content-Disposition": "attachment; filename=shop_risk_report.pdf"},
            )
        except ImportError:
            raise HTTPException(500, "reportlab not installed. Use CSV format.")
