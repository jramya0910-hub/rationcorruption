from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime
from ..database import get_db
from ..models import Beneficiary, Shop, Transaction, Complaint, StockInventory
from ..models.complaint import ComplaintStatus
from ..schemas.schemas import ComplaintCreate
from ..utils.auth import require_role
from ..utils.response import success
from ..ai.complaint_nlp import categorize_complaint

router = APIRouter(prefix="/beneficiary", tags=["Beneficiary"])


@router.get("/{beneficiary_id}/entitlement")
async def get_entitlement(
    beneficiary_id: str,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_role("beneficiary", "officer")),
):
    result = await db.execute(
        select(Beneficiary, Shop)
        .join(Shop, Beneficiary.assigned_shop_id == Shop.shop_id, isouter=True)
        .where(Beneficiary.beneficiary_id == beneficiary_id)
    )
    row = result.first()
    if not row:
        raise HTTPException(404, "Beneficiary not found")
    ben, shop = row
    return success({
        "beneficiary_id": str(ben.beneficiary_id),
        "name": ben.name,
        "ration_card_number": ben.ration_card_number,
        "family_members": ben.family_members,
        "monthly_entitlement_kg": float(ben.monthly_entitlement_kg),
        "assigned_shop_id": str(ben.assigned_shop_id) if ben.assigned_shop_id else None,
        "shop_name": shop.shop_name if shop else None,
        "shop_location": shop.location if shop else None,
    })


@router.get("/{beneficiary_id}/receipts")
async def get_receipts(
    beneficiary_id: str,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_role("beneficiary", "officer")),
):
    result = await db.execute(
        select(Transaction, Shop)
        .join(Shop, Transaction.shop_id == Shop.shop_id)
        .where(Transaction.beneficiary_id == beneficiary_id)
        .order_by(Transaction.transaction_date.desc())
        .limit(50)
    )
    rows = result.all()
    receipts = [
        {
            "transaction_id": str(t.transaction_id),
            "grain_type": t.grain_type.value,
            "quantity_given_kg": float(t.quantity_given_kg),
            "transaction_date": t.transaction_date.isoformat(),
            "qr_scan_verified": t.qr_scan_verified,
            "shop_name": s.shop_name,
        }
        for t, s in rows
    ]
    return success({"receipts": receipts})


@router.get("/{beneficiary_id}/stock-availability")
async def get_stock_availability(
    beneficiary_id: str,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_role("beneficiary", "officer")),
):
    ben_result = await db.execute(
        select(Beneficiary).where(Beneficiary.beneficiary_id == beneficiary_id)
    )
    ben = ben_result.scalar_one_or_none()
    if not ben or not ben.assigned_shop_id:
        raise HTTPException(404, "Beneficiary or shop not found")

    inv_result = await db.execute(
        select(StockInventory).where(StockInventory.shop_id == ben.assigned_shop_id)
    )
    inventory = inv_result.scalars().all()
    stock = [
        {
            "grain_type": i.grain_type.value,
            "remaining_stock_kg": float(i.stock_received_kg or 0) - float(i.stock_distributed_kg or 0),
            "available": (float(i.stock_received_kg or 0) - float(i.stock_distributed_kg or 0)) > 0,
        }
        for i in inventory
    ]
    return success({"stock_availability": stock, "shop_id": str(ben.assigned_shop_id)})


@router.post("/complaint")
async def submit_complaint(
    payload: ComplaintCreate,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_role("beneficiary")),
):
    from ..models.complaint import Complaint, ComplaintStatus
    beneficiary_id = user["sub"]

    # AI categorization
    ai_category = categorize_complaint(payload.description or "")

    complaint = Complaint(
        beneficiary_id=beneficiary_id,
        shop_id=str(payload.shop_id),
        complaint_type=payload.complaint_type.value,
        description=payload.description,
        status=ComplaintStatus.OPEN,
        ai_category=ai_category,
    )
    db.add(complaint)
    await db.commit()
    await db.refresh(complaint)
    return success({"complaint_id": str(complaint.complaint_id), "ai_category": ai_category}, "Complaint submitted")


@router.get("/{beneficiary_id}/complaints")
async def get_complaints(
    beneficiary_id: str,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_role("beneficiary", "officer")),
):
    from ..models.complaint import Complaint
    result = await db.execute(
        select(Complaint, Shop)
        .join(Shop, Complaint.shop_id == Shop.shop_id)
        .where(Complaint.beneficiary_id == beneficiary_id)
        .order_by(Complaint.created_at.desc())
    )
    rows = result.all()
    complaints = [
        {
            "complaint_id": str(c.complaint_id),
            "shop_name": s.shop_name,
            "complaint_type": c.complaint_type.value,
            "description": c.description,
            "status": c.status.value,
            "ai_category": c.ai_category,
            "created_at": c.created_at.isoformat(),
            "resolved_at": c.resolved_at.isoformat() if c.resolved_at else None,
        }
        for c, s in rows
    ]
    return success({"complaints": complaints})
