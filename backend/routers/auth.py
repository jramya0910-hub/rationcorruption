from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..database import get_db
from ..models import Beneficiary, Shop
from ..models.fraud_alert import Officer
from ..schemas.schemas import LoginRequest
from ..utils.auth import verify_password, create_token
from ..utils.response import success, error

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login")
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    role = payload.role.lower()

    if role == "beneficiary":
        result = await db.execute(
            select(Beneficiary).where(Beneficiary.ration_card_number == payload.username)
        )
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=401, detail="Beneficiary not found")
        if not verify_password(payload.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        token = create_token({"sub": str(user.beneficiary_id), "role": "beneficiary", "name": user.name})
        return success({
            "access_token": token, "token_type": "bearer",
            "role": "beneficiary", "user_id": str(user.beneficiary_id), "name": user.name
        }, "Login successful")

    elif role == "shopkeeper":
        result = await db.execute(
            select(Shop).where(Shop.shop_name == payload.username)
        )
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=401, detail="Shop not found")
        if not verify_password(payload.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        token = create_token({"sub": str(user.shop_id), "role": "shopkeeper", "name": user.shop_name})
        return success({
            "access_token": token, "token_type": "bearer",
            "role": "shopkeeper", "user_id": str(user.shop_id), "name": user.shop_name
        }, "Login successful")

    elif role == "officer":
        result = await db.execute(
            select(Officer).where(Officer.email == payload.username)
        )
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=401, detail="Officer not found")
        if not verify_password(payload.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        token = create_token({"sub": str(user.officer_id), "role": "officer", "name": user.name})
        return success({
            "access_token": token, "token_type": "bearer",
            "role": "officer", "user_id": str(user.officer_id), "name": user.name
        }, "Login successful")

    else:
        raise HTTPException(status_code=400, detail="Invalid role. Use: beneficiary, shopkeeper, officer")


@router.post("/logout")
async def logout():
    return success({}, "Logged out successfully")
