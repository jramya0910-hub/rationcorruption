from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, UUID4, field_validator
import enum


# ── Common response wrapper ────────────────────────────────────────────────────

class APIResponse(BaseModel):
    status: str = "success"
    data: object = {}
    message: str = ""


# ── Enums ──────────────────────────────────────────────────────────────────────

class GrainTypeEnum(str, enum.Enum):
    RICE  = "RICE"
    WHEAT = "WHEAT"
    SUGAR = "SUGAR"
    OIL   = "OIL"

class RiskLevelEnum(str, enum.Enum):
    LOW    = "LOW"
    MEDIUM = "MEDIUM"
    HIGH   = "HIGH"

class ComplaintTypeEnum(str, enum.Enum):
    UNDERWEIGHT   = "UNDERWEIGHT"
    POOR_QUALITY  = "POOR_QUALITY"
    OVERCHARGING  = "OVERCHARGING"
    NOT_AVAILABLE = "NOT_AVAILABLE"
    OTHER         = "OTHER"

class ComplaintStatusEnum(str, enum.Enum):
    OPEN         = "OPEN"
    UNDER_REVIEW = "UNDER_REVIEW"
    RESOLVED     = "RESOLVED"

class SeverityEnum(str, enum.Enum):
    LOW      = "LOW"
    MEDIUM   = "MEDIUM"
    HIGH     = "HIGH"
    CRITICAL = "CRITICAL"


# ── Auth ───────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str          # ration_card_number | shop_id(email) | officer email
    password: str
    role: str              # beneficiary | shopkeeper | officer

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    user_id: str
    name: str


# ── Beneficiary ────────────────────────────────────────────────────────────────

class BeneficiaryOut(BaseModel):
    beneficiary_id: UUID4
    ration_card_number: str
    name: str
    phone: Optional[str]
    address: Optional[str]
    family_members: int
    assigned_shop_id: Optional[UUID4]
    monthly_entitlement_kg: float
    created_at: datetime

    class Config:
        from_attributes = True

class EntitlementOut(BaseModel):
    beneficiary_id: UUID4
    name: str
    monthly_entitlement_kg: float
    family_members: int
    assigned_shop_id: Optional[UUID4]
    shop_name: Optional[str]


# ── Shop / Inventory ───────────────────────────────────────────────────────────

class ShopOut(BaseModel):
    shop_id: UUID4
    shop_name: str
    owner_name: str
    location: str
    district: str
    risk_score: float
    risk_level: RiskLevelEnum
    created_at: datetime

    class Config:
        from_attributes = True

class InventoryOut(BaseModel):
    inventory_id: UUID4
    shop_id: UUID4
    grain_type: GrainTypeEnum
    stock_received_kg: float
    stock_distributed_kg: float
    remaining_stock_kg: float
    last_updated: datetime

    class Config:
        from_attributes = True

class InventoryUpdateRequest(BaseModel):
    grain_type: GrainTypeEnum
    stock_received_kg: Optional[float] = None
    stock_distributed_kg: Optional[float] = None


# ── Transactions ───────────────────────────────────────────────────────────────

class TransactionOut(BaseModel):
    transaction_id: UUID4
    shop_id: UUID4
    beneficiary_id: UUID4
    grain_type: GrainTypeEnum
    quantity_given_kg: float
    transaction_date: datetime
    qr_scan_verified: bool
    beneficiary_name: Optional[str] = None
    ration_card_number: Optional[str] = None

    class Config:
        from_attributes = True

class ScanTransactionRequest(BaseModel):
    beneficiary_id: UUID4
    grain_type: GrainTypeEnum
    quantity_given_kg: float
    qr_scan_verified: bool = True


# ── Complaints ─────────────────────────────────────────────────────────────────

class ComplaintCreate(BaseModel):
    shop_id: UUID4
    complaint_type: ComplaintTypeEnum
    description: Optional[str] = None

class ComplaintOut(BaseModel):
    complaint_id: UUID4
    beneficiary_id: UUID4
    shop_id: UUID4
    complaint_type: ComplaintTypeEnum
    description: Optional[str]
    status: ComplaintStatusEnum
    ai_category: Optional[str]
    created_at: datetime
    resolved_at: Optional[datetime]
    shop_name: Optional[str] = None
    beneficiary_name: Optional[str] = None

    class Config:
        from_attributes = True

class ComplaintResolveRequest(BaseModel):
    complaint_id: UUID4


# ── Fraud Alerts ───────────────────────────────────────────────────────────────

class FraudAlertOut(BaseModel):
    alert_id: UUID4
    shop_id: UUID4
    alert_type: str
    description: Optional[str]
    severity: SeverityEnum
    is_reviewed: bool
    created_at: datetime
    shop_name: Optional[str] = None

    class Config:
        from_attributes = True


# ── Stock Prediction ───────────────────────────────────────────────────────────

class PredictionOut(BaseModel):
    prediction_id: UUID4
    shop_id: UUID4
    grain_type: GrainTypeEnum
    predicted_demand_kg: float
    prediction_month: datetime
    created_at: datetime
    shop_name: Optional[str] = None

    class Config:
        from_attributes = True


# ── AI ─────────────────────────────────────────────────────────────────────────

class FraudDetectionRequest(BaseModel):
    shop_id: UUID4

class FraudDetectionResult(BaseModel):
    shop_id: str
    anomaly_score: float
    is_fraud_suspected: bool
    reason_text: str
    risk_score: float
    risk_level: str

class StockPredictRequest(BaseModel):
    shop_id: UUID4
    grain_type: GrainTypeEnum

class ComplaintCategorizeRequest(BaseModel):
    description: str

class ComplaintCategorizeResult(BaseModel):
    predicted_category: str
    confidence: float


# ── Officer Dashboard ──────────────────────────────────────────────────────────

class DashboardSummary(BaseModel):
    total_shops: int
    total_beneficiaries: int
    active_alerts: int
    open_complaints: int
    high_risk_shops: int
