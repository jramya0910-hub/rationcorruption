import uuid
import enum
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Numeric, Boolean, Text,
    ForeignKey, Enum as SAEnum, DateTime, Date, Computed
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from ..database import Base


class GrainType(str, enum.Enum):
    RICE = "RICE"
    WHEAT = "WHEAT"
    SUGAR = "SUGAR"
    OIL = "OIL"


class RiskLevel(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class Shop(Base):
    __tablename__ = "shops"

    shop_id       = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shop_name     = Column(String(200), nullable=False)
    owner_name    = Column(String(200), nullable=False)
    location      = Column(Text, nullable=False)
    district      = Column(String(100), nullable=False)
    risk_score    = Column(Numeric(5, 2), default=0.0)
    risk_level    = Column(SAEnum(RiskLevel, name="risk_level_enum"), default=RiskLevel.LOW)
    password_hash = Column(String(255), nullable=False)
    created_at    = Column(DateTime, default=datetime.utcnow)

    beneficiaries    = relationship("Beneficiary", back_populates="assigned_shop")
    inventory        = relationship("StockInventory", back_populates="shop")
    transactions     = relationship("Transaction", back_populates="shop")
    complaints       = relationship("Complaint", back_populates="shop")
    fraud_alerts     = relationship("FraudAlert", back_populates="shop")
    stock_predictions = relationship("StockPrediction", back_populates="shop")
