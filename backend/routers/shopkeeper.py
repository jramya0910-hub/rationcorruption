from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime
from ..database import get_db
from ..models import Shop, StockInventory, Transaction, Beneficiary
from ..schemas.schemas import InventoryUpdateRequest, ScanTransactionRequest
from ..utils.auth import require_role
from ..utils.response import success

router = APIRouter(prefix="/shop", tags=["Shopkeeper"])


@router.post("/stock/update")
async def update_stock(
    payload: InventoryUpdateRequest,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_role("shopkeeper", "officer")),
):
    shop_id = user["sub"]
    result = await db.execute(
        select(StockInventory).where(
            StockInventory.shop_id == shop_id,
            StockInventory.grain_type == payload.grain_type.value,
        )
    )
    inv = result.scalar_one_or_none()

    if not inv:
        inv = StockInventory(
            shop_id=shop_id,
            grain_type=payload.grain_type.value,
            stock_received_kg=payload.stock_received_kg or 0,
            stock_distributed_kg=payload.stock_distributed_kg or 0,
        )
        db.add(inv)
    else:
        if payload.stock_received_kg is not None:
            inv.stock_received_kg = float(inv.stock_received_kg or 0) + payload.stock_received_kg
        if payload.stock_distributed_kg is not None:
            inv.stock_distributed_kg = float(inv.stock_distributed_kg or 0) + payload.stock_distributed_kg
        inv.last_updated = datetime.utcnow()

    await db.commit()
    await db.refresh(inv)
    return success({
        "grain_type": inv.grain_type.value,
        "stock_received_kg": float(inv.stock_received_kg),
        "stock_distributed_kg": float(inv.stock_distributed_kg),
        "remaining_stock_kg": float(inv.stock_received_kg or 0) - float(inv.stock_distributed_kg or 0),
    }, "Stock updated")


@router.post("/transaction/scan")
async def scan_transaction(
    payload: ScanTransactionRequest,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_role("shopkeeper")),
):
    shop_id = user["sub"]

    # Verify beneficiary exists and is assigned to this shop
    result = await db.execute(
        select(Beneficiary).where(
            Beneficiary.beneficiary_id == str(payload.beneficiary_id),
            Beneficiary.assigned_shop_id == shop_id,
        )
    )
    ben = result.scalar_one_or_none()
    if not ben:
        raise HTTPException(404, "Beneficiary not found or not assigned to this shop")

    # Record transaction
    txn = Transaction(
        shop_id=shop_id,
        beneficiary_id=str(payload.beneficiary_id),
        grain_type=payload.grain_type.value,
        quantity_given_kg=payload.quantity_given_kg,
        qr_scan_verified=payload.qr_scan_verified,
    )
    db.add(txn)

    # Update distributed stock
    inv_result = await db.execute(
        select(StockInventory).where(
            StockInventory.shop_id == shop_id,
            StockInventory.grain_type == payload.grain_type.value,
        )
    )
    inv = inv_result.scalar_one_or_none()
    if inv:
        inv.stock_distributed_kg = float(inv.stock_distributed_kg or 0) + payload.quantity_given_kg
        inv.last_updated = datetime.utcnow()

    await db.commit()
    await db.refresh(txn)
    return success({"transaction_id": str(txn.transaction_id)}, "Transaction recorded")


@router.get("/{shop_id}/inventory")
async def get_inventory(
    shop_id: str,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_role("shopkeeper", "officer")),
):
    result = await db.execute(
        select(StockInventory).where(StockInventory.shop_id == shop_id)
    )
    inventory = result.scalars().all()
    LOW_STOCK_THRESHOLD = 50.0
    data = [
        {
            "inventory_id": str(i.inventory_id),
            "grain_type": i.grain_type.value,
            "stock_received_kg": float(i.stock_received_kg),
            "stock_distributed_kg": float(i.stock_distributed_kg),
            "remaining_stock_kg": float(i.stock_received_kg or 0) - float(i.stock_distributed_kg or 0),
            "low_stock_alert": (float(i.stock_received_kg or 0) - float(i.stock_distributed_kg or 0)) < LOW_STOCK_THRESHOLD,
        }
        for i in inventory
    ]
    return success({"inventory": data})


@router.get("/{shop_id}/transactions")
async def get_transactions(
    shop_id: str,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_role("shopkeeper", "officer")),
):
    result = await db.execute(
        select(Transaction, Beneficiary)
        .join(Beneficiary, Transaction.beneficiary_id == Beneficiary.beneficiary_id)
        .where(Transaction.shop_id == shop_id)
        .order_by(Transaction.transaction_date.desc())
        .limit(100)
    )
    rows = result.all()
    data = [
        {
            "transaction_id": str(t.transaction_id),
            "beneficiary_name": b.name,
            "ration_card_number": b.ration_card_number,
            "grain_type": t.grain_type.value,
            "quantity_given_kg": float(t.quantity_given_kg),
            "transaction_date": t.transaction_date.isoformat(),
            "qr_scan_verified": t.qr_scan_verified,
        }
        for t, b in rows
    ]
    return success({"transactions": data})
